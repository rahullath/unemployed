# Power BI session: one pass, about an hour

Do this on Windows. Everything below is in the order to do it. The expected numbers are in the checks, so you know each step worked.

## Before you boot Windows

- Have the SQL password to hand (never put it in a file or a commit).
- Have this repo's `measures.dax` and `summaries/gaps.csv` where Windows can reach them: install Git for Windows and `git clone https://github.com/rahullath/unemployed`, or open the files on GitHub and copy the text.
- Azure portal, SQL server `ket`, **Networking**: add the client IP of the machine you will use. If you are on the same network as before, it is the same IP.

## 1. Install and connect (10 min)

1. Install **Power BI Desktop** from the Microsoft Store.
2. Open `free-sql-db-8925777.pbids` (the file you uploaded earlier), or **Get data > Azure SQL database** with server `ket.database.windows.net` and database `free-sql-db-8925777`.
3. Connectivity mode: **Import**, not DirectQuery.
4. Credentials: **Database** tab, user `CloudSAc9ca18de`, your password.
5. In the navigator tick `fact_listing` and `dim_source`, then **Load**.

Check: **Data** view shows `fact_listing` with 1,908 rows.

## 2. Model (10 min)

1. **Model** view: drag `fact_listing[source]` onto `dim_source[source]`. It should be many-to-one, single direction.
2. **Home > Enter data / New table**, then paste: `dim_date = CALENDAR ( DATE ( 2026, 9, 1 ), DATE ( 2026, 12, 31 ) )`. Drag `fact_listing[date_found]` onto `dim_date[Date]`.
3. **Get data > Text/CSV**, load `summaries/gaps.csv` as `gaps`. It stands alone with no relationship.
4. Select `fact_listing[has_closing]`, set the data type to **True/False** if it loaded as a number.

## 3. Measures (15 min)

Use **Home > New measure** (or **New table** for `Funnel`). Paste each block from `measures.dax` one at a time. Pasting the whole file at once fails, because the editor takes one definition per box.

Put them all in a `fact_listing` home table, or make an empty table called `_Measures`.

Checks. Put each in a Card visual on a scratch page:

| Measure | Expect |
| --- | --- |
| Listings | 1,908 |
| Read | 185 |
| Passed | 133 |
| Applied | 88 |
| Interviews | 1 |
| Has closing date | 35 |
| Never touched | 1,609 |
| Below floor | 196 |
| Readable rate | 9.7% |
| Closing rate | 1.8% |

If a number differs, stop. The usual cause is `has_closing` loading as text or a missing relationship. Fix it before building pages.

## 4. Page 1: what the board says and what we could read (10 min)

Rename the page `1 What we could read`.

- Three **Card** visuals: `Listings`, `Readable rate`, `Closing rate`.
- A **Clustered bar chart**: Y axis `dim_source[source]`, X axis `Listings` and `Has closing date`. Sort by Listings, descending.
- A **Table**: `dim_source[source]`, `dim_source[readable_by_routine]`, `Listings`, `Read`, `Has closing date`.
- A **Slicer** on `dim_source[readable_by_routine]`.

Title the page with the claim: "Reed and Adzuna supply most listings; almost no source gives a closing date."

## 5. Page 2: the funnel (5 min)

Rename it `2 Funnel`.

- A **Funnel** visual: Category `Funnel[stage]`, Values `Funnel value`.
- Select `Funnel[stage]` in the Data pane, then **Column tools > Sort by column > order**, so the stages run found to interview.
- Cards: `Never touched`, `Apply rate`.

Check: the funnel reads 1,908, 185, 133, 88, 1.

## 6. Page 3: why adverts fail (10 min)

Rename it `3 Why adverts fail`.

- A **Bar chart**: Y axis `fact_listing[vet_fail_reason]`, X axis `Listings`. In **Filters on this visual** set `vet_state` is `failed`. Check: closed 18, too many applicants 16.
- A **Bar chart** from the stand-alone `gaps` table: Y axis `gaps[gap]`, X axis `gaps[count]`. Check: Azure 18 is the top bar.
- Cards: `Below floor`, `Age at found` (format it as a whole number of days).

## 7. Save and capture (5 min)

1. **File > Save as** `job-board-counted.pbix`.
2. For each page, take a full-window screenshot (Win+Shift+S, or Snipping Tool) and save as `screenshots/page1.png`, `page2.png`, `page3.png`. Drop sensitive fields: the pages show no company, URL or notes, so there is nothing to blur. Check before saving.
3. Do not use **Publish**. A school account may not allow it, and the counted page does not need it.

## 8. Get the files into the repo

In the `unemployed` clone on Windows:

```
mkdir screenshots
copy job-board-counted.pbix .
git add job-board-counted.pbix screenshots
git commit -m "Add Power BI report and screenshots"
git push
```

If git is not set up, use **Add file > Upload files** on github.com/rahullath/unemployed and drop in the `.pbix` and the three PNGs.

The `.pbix` contains the imported rows (aggregates would be safer). It has no company, URL or notes columns, since the load file never had them. Check **Home > Transform data** shows only the columns in `schema.sql` before you push.

## Done means

- The three pages exist, with every check above matching.
- `job-board-counted.pbix` and `screenshots/page1-3.png` are in the repo.
- Only then add the CV bullet: "Built an Azure SQL and Power BI model (DAX measures, star schema) of 1,900 job listings; published the counted findings, source and limits."
- Delete the Azure resources when you are finished: resource group, then the budget alert.
