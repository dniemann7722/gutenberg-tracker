#!/usr/bin/env python3
"""
Scrape Project Gutenberg's "Top 100" page and append rankings to a running
CSV history file.

Tracks two of the three ebook windows Gutenberg publishes: "last 7 days"
and "last 30 days". The "yesterday" window is intentionally skipped -
sampled weekly it's mostly single-day noise, not a useful trend signal.

Which window(s) get scraped in a given run is controlled by the
--windows argument (a comma-separated list of anchor names: books-last7,
books-last30). This lets the same script serve two different schedules -
a weekly run for the 7-day window, and a monthly run for the 30-day
window - without duplicating code. See the accompanying GitHub Actions
workflow for how that's wired up.

Designed to run unattended (e.g. via GitHub Actions on a schedule), so it
avoids third-party libraries beyond the Python standard library; HTML
parsing is done with plain regular expressions since Project Gutenberg's
page structure is simple and has been stable for years.
"""

import argparse
import csv
import datetime
import html
import os
import re
import sys
import urllib.request

URL = "https://www.gutenberg.org/browse/scores/top"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_PATH = os.path.join(DATA_DIR, "top100_books.csv")

# Maps the anchor name Gutenberg uses for each section to a short label
# we'll store in the CSV. ("books-last1" / "yesterday" is deliberately
# excluded - see module docstring.)
WINDOWS = {
    "books-last7": "last_7_days",
    "books-last30": "last_30_days",
}

DEFAULT_WINDOWS = "books-last7"

CSV_FIELDS = ["scrape_date", "window", "rank", "ebook_id", "title_and_author", "downloads"]


def fetch_html(url: str) -> str:
    """Download the page HTML. Uses a descriptive User-Agent since Gutenberg
    (reasonably) blocks generic/blank ones."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "textualheritage.com top100-tracker (personal research script)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_section(html: str, anchor_name: str) -> str:
    """Return the chunk of HTML between one named anchor and the next
    heading, which is where a given Top 100 list lives."""
    # Sections are marked either as name="books-last1" or id="books-last1"
    # depending on Gutenberg's current markup; check for both.
    pattern = re.compile(
        r'(?:name|id)=["\']' + re.escape(anchor_name) + r'["\'].*?(?=<h[1-3][ >]|\Z)',
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html)
    if not match:
        return ""
    return match.group(0)


def parse_list_items(section_html: str):
    """Pull (ebook_id, title_and_author, downloads) tuples out of a
    section's <li><a href="/ebooks/ID">Title by Author (COUNT)</a></li>
    entries. Falls back gracefully if a row doesn't match the usual shape."""
    items = []
    li_pattern = re.compile(r'<li>\s*<a href="[^"]*?/ebooks/(\d+)"[^>]*>(.*?)</a>\s*</li>', re.DOTALL)
    for ebook_id, raw_text in li_pattern.findall(section_html):
        text = re.sub(r"<[^>]+>", "", raw_text)  # strip any nested tags
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        count_match = re.search(r"\((\d+)\)\s*$", text)
        if count_match:
            downloads = count_match.group(1)
            title_and_author = text[: count_match.start()].strip()
        else:
            downloads = ""
            title_and_author = text
        items.append((ebook_id, title_and_author, downloads))
    return items


def load_existing_keys(csv_path: str):
    """Read (scrape_date, window) pairs already recorded, so a re-run on
    the same day doesn't create duplicate rows."""
    keys = set()
    if os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                keys.add((row["scrape_date"], row["window"]))
    return keys


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--windows",
        default=DEFAULT_WINDOWS,
        help=(
            "Comma-separated list of anchor names to scrape this run. "
            f"Choices: {', '.join(WINDOWS.keys())}. "
            f"Defaults to '{DEFAULT_WINDOWS}'."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    requested = [w.strip() for w in args.windows.split(",") if w.strip()]
    unknown = [w for w in requested if w not in WINDOWS]
    if unknown:
        print(f"ERROR: unrecognized window(s) {unknown}. "
              f"Valid choices: {list(WINDOWS.keys())}", file=sys.stderr)
        sys.exit(1)
    windows_to_scrape = {w: WINDOWS[w] for w in requested} or WINDOWS

    today = datetime.date.today().isoformat()

    try:
        html_text = fetch_html(URL)
    except Exception as exc:  # noqa: BLE001 - want the run to fail loudly in Actions logs
        print(f"ERROR: failed to fetch {URL}: {exc}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)
    already_scraped = load_existing_keys(CSV_PATH)

    new_rows = []
    for anchor_name, window_label in windows_to_scrape.items():
        if (today, window_label) in already_scraped:
            print(f"Skipping {window_label}: already recorded for {today}")
            continue

        section_html = extract_section(html_text, anchor_name)
        items = parse_list_items(section_html)

        if not items:
            print(f"WARNING: found 0 entries for '{window_label}' "
                  f"(anchor '{anchor_name}') - Gutenberg's page layout may have changed.",
                  file=sys.stderr)
            continue

        for rank, (ebook_id, title_and_author, downloads) in enumerate(items, start=1):
            new_rows.append({
                "scrape_date": today,
                "window": window_label,
                "rank": rank,
                "ebook_id": ebook_id,
                "title_and_author": title_and_author,
                "downloads": downloads,
            })
        print(f"Parsed {len(items)} entries for '{window_label}'")

    if not new_rows:
        print("Nothing new to write.")
        return

    file_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)

    print(f"Wrote {len(new_rows)} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
