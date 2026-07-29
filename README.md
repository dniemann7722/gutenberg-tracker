# Gutenberg Top 100 Tracker

Scrapes Project Gutenberg's [Top 100](https://www.gutenberg.org/browse/scores/top)
page on a weekly schedule and appends the rankings to `data/top100_books.csv`,
so you can eventually see which titles are steady perennials and which ones
spike and fade.

## One-time setup

1. **Create a GitHub account** at github.com if you don't already have one.
2. **Create a new repository** (the "+" icon, top right, then "New repository").
   Name it something like `gutenberg-tracker`. It can be public or private;
   public is fine since this is just download-count data, not anything
   sensitive.
3. **Upload these files**, keeping the folder structure intact:
   - `scrape.py`
   - `requirements.txt`
   - `README.md`
   - `.github/workflows/scrape.yml`

   The easiest way for a first repo: on the repository's page, click
   "Add file" > "Upload files", drag in `scrape.py`, `requirements.txt`,
   and `README.md`, and commit. Then repeat for the workflow file — GitHub
   will let you type the folder path `.github/workflows/scrape.yml` as the
   filename when uploading, and it will create those folders automatically.
4. **That's it.** The workflow is scheduled for Monday mornings (09:00 UTC).
   You can also trigger it immediately to test: go to the "Actions" tab,
   click "Scrape Gutenberg Top 100" in the left sidebar, then "Run workflow".

After a run finishes, check the "Actions" tab for a green checkmark, and
look in the `data/` folder of your repo for `top100_books.csv` — each run
appends new rows rather than overwriting.

## Adjusting the schedule

Edit the `cron` line in `.github/workflows/scrape.yml`. Cron format is
`minute hour day month weekday`, always in UTC. For example:
- `"0 9 * * 1"` = every Monday at 9am UTC (current setting)
- `"0 9 * * *"` = every day at 9am UTC
- `"0 9 1 * *"` = the 1st of every month at 9am UTC

## What's in the CSV

| column | meaning |
|---|---|
| `scrape_date` | the date (UTC) the scrape ran |
| `window` | which Gutenberg list this row came from: `yesterday`, `last_7_days`, or `last_30_days` |
| `rank` | position in that list, 1-100 |
| `ebook_id` | Gutenberg's ebook number — the stable identifier if a title's wording ever changes |
| `title_and_author` | the raw title/author text as Gutenberg lists it |
| `downloads` | the download count Gutenberg reports for that entry |

Because some titles appear under more than one Gutenberg edition (different
`ebook_id`s), track trends by `ebook_id` rather than by title text alone if
you want to be precise.

## Notes

- If a run's log shows a "WARNING: found 0 entries" message, Gutenberg has
  likely changed its page layout and `scrape.py` will need a small update
  to match. Feel free to bring the warning text back for help fixing it.
- The scraper only needs the Python standard library, so there is nothing
  to install locally if you ever want to test-run it on your own computer:
  just `python3 scrape.py` from inside the folder.
