# Gutenberg Top 100 Tracker

Scrapes Project Gutenberg's [Top 100](https://www.gutenberg.org/browse/scores/top)
page and appends the rankings to `data/top100_books.csv`, so you can
eventually see which titles are steady perennials and which ones spike
and fade.

## Which lists get tracked, and how often

Project Gutenberg publishes three ebook windows: "yesterday," "last 7
days," and "last 30 days." This tracker only keeps two of them, on two
different schedules:

- **"last 7 days," scraped weekly** (every Monday). A 7-day window
  sampled every 7 days barely overlaps with the previous sample, so
  almost every row is genuinely new information.
- **"last 30 days," scraped monthly** (the 1st of each month). This
  rolling window moves slowly; sampling it more often than monthly would
  mostly just re-report days already captured in the prior sample.

The **"yesterday"** list is deliberately skipped. It's the noisiest of
the three - a single day's numbers can be skewed by one class assignment
or one bot crawl - and doesn't add much toward the perennial-vs-fashion
question this data set is for.

This keeps the CSV growing at roughly 100 rows a week most weeks, and an
extra 100 once a month, instead of 300 rows every single week.

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
   and `README.md`, and commit. For the workflow file, upload it
   separately and type the folder path `.github/workflows/scrape.yml` as
   the filename - GitHub will create those folders automatically. (If you
   ever upload it to the wrong spot, you can fix it afterward: open the
   file on GitHub, click the pencil "edit" icon, and change the filename
   field at the top to the full path.)
4. **That's it.** The workflow runs on its own schedule from here - no
   need to keep your computer on. You can also trigger it immediately to
   test: go to the "Actions" tab, click "Scrape Gutenberg Top 100" in the
   left sidebar, then "Run workflow," and pick which window(s) to scrape
   from the dropdown.

After a run finishes, check the "Actions" tab for a green checkmark, and
look in the `data/` folder of your repo for `top100_books.csv` - each run
appends new rows rather than overwriting.

## Adjusting the schedule

Edit the two `cron` lines in `.github/workflows/scrape.yml`. Cron format
is `minute hour day month weekday`, always in UTC. Current settings:

- `"0 9 * * 1"` = every Monday at 9am UTC (scrapes `last_7_days`)
- `"0 9 1 * *"` = the 1st of every month at 9am UTC (scrapes `last_30_days`)

If you change which day/date these fire on, also update the matching
comparison inside the "Determine which window(s) to scrape" step in the
same file, so the workflow still knows which cron line just fired.

## What's in the CSV

| column | meaning |
|---|---|
| `scrape_date` | the date (UTC) the scrape ran |
| `window` | which Gutenberg list this row came from: `last_7_days` or `last_30_days` |
| `rank` | position in that list, 1-100 |
| `ebook_id` | Gutenberg's ebook number - the stable identifier if a title's wording ever changes |
| `title_and_author` | the raw title/author text as Gutenberg lists it |
| `downloads` | the download count Gutenberg reports for that entry |

Because some titles appear under more than one Gutenberg edition (different
`ebook_id`s), track trends by `ebook_id` rather than by title text alone if
you want to be precise.

## Running or scraping manually

`scrape.py` takes an optional `--windows` argument if you ever want to run
it yourself (locally, or via a manual "Run workflow" click):

```
python3 scrape.py --windows books-last7
python3 scrape.py --windows books-last30
python3 scrape.py --windows books-last7,books-last30
```

It defaults to `books-last7` if you omit the argument.

## Notes

- If a run's log shows a "WARNING: found 0 entries" message, Gutenberg has
  likely changed its page layout and `scrape.py` will need a small update
  to match. Feel free to bring the warning text back for help fixing it.
- The scraper only needs the Python standard library, so there is nothing
  to install locally if you ever want to test-run it on your own computer:
  just `python3 scrape.py` from inside the folder.
