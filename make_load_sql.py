"""Build out/load.sql: schema.sql with INSERTs for out/clean_listings.csv at the LOAD marker.

Run parse_tracker.py first. Then open out/load.sql in Azure Data Studio (or the portal Query editor) and run it.
out/ is git-ignored. The file holds no company, URL or notes columns."""
import csv, pathlib

ROOT = pathlib.Path(__file__).parent
COLS = ["date_found", "source", "title_family", "location_band", "contract", "pay_annual", "posted_date",
        "closes_date", "has_closing", "vet_state", "vet_fail_reason", "status", "date_applied"]
NUM = {"pay_annual", "has_closing"}

def lit(col, v):
    if v == "":
        return "NULL"
    return v if col in NUM else "'" + v.replace("'", "''") + "'"

rows = list(csv.DictReader(open(ROOT / "out" / "clean_listings.csv", encoding="utf-8")))
stmts = []
for i in range(0, len(rows), 500):  # SQL Server allows 1,000 rows per VALUES list
    vals = ",\n".join("(" + ",".join(lit(c, r[c]) for c in COLS) + ")" for r in rows[i:i + 500])
    stmts.append(f"INSERT INTO stg_listing ({','.join(COLS)}) VALUES\n{vals};")
sql = (ROOT / "schema.sql").read_text().replace("-- LOAD:stg_listing", "\n".join(stmts))
(ROOT / "out" / "load.sql").write_text(sql, encoding="utf-8")
print(f"out/load.sql: {len(rows)} rows")
