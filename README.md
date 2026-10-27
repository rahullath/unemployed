# The job board, counted

A job board promises to tell you what is open and whether you fit. Over five weeks it handed this search 1,908 listings. It showed a closing date for 35 of them, an advert we could actually read for 185, and led to 1 interview.

Weltschmerz build nine. The page is `docs/index.html`: plain HTML and CSS, no JavaScript, one mark per 50 listings, part marks clipped and never shrunk.

## Limits to respect

- One candidate, one region, five weeks. This is not a market study.
- The tracker captures what the scrapers could read. A missing closing date means we could not read one, not that the board had none.
- Aggregates only. No company names, links or notes are published, and the row-level file stays out of the repository.

## What is here

| File | Purpose |
| --- | --- |
| `parse_tracker.py` | Reads the tracker CSV, writes `out/clean_listings.csv` (git-ignored) and the aggregates in `summaries/` |
| `make_load_sql.py` | Builds `out/load.sql`: `schema.sql` with the rows inserted |
| `schema.sql` | Azure SQL staging table, `dim_source`, `fact_listing` and the summary queries |
| `measures.dax` | Power BI measures |
| `build_page.py` | Builds `docs/index.html` from `summaries/` |
| `tests/test_baseline.py` | Fails if a published count drifts from the baseline |

## Rerun it

```
python3 parse_tracker.py path/to/job_search_tracker.csv
python3 tests/test_baseline.py
python3 build_page.py
```

Then `python3 make_load_sql.py`, open `out/load.sql` in Azure Data Studio and run it (it creates the tables and loads the rows). Add `measures.dax` in Power BI Desktop, using Import mode.

## Method notes

- Source names are merged (`jobspy(linkedin)`, `jobspy:linkedin` and `linkedin` are one source).
- Pay is the first £ figure in the notes; hourly x 1,950, daily x 230 (from `tools/rank_jobs.py` in the job search repository).
- "Read" means the notes hold a `VET` or `VET-FAIL` line. Failure reasons are grouped from that text; "3+ or 5+ years asked" joins two wordings and counts 6, where the plan's baseline counted 7.
- Applied counts the statuses applied (56), rejected (31) and interview invite (1): 88.

## Not done yet

The Azure SQL database and the Power BI `.pbix` with its screenshots need your accounts and Power BI Desktop (Windows). Add the CV bullet only once they are live.

Design: the Weltschmerz design system. Fonts are not loaded; the page falls back to system faces. Licence: MIT for code; the figures and text are offered under CC BY 4.0, change that line in `build_page.py` if you prefer another.
