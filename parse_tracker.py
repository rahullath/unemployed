"""Parse job_search_tracker.csv into a clean listing table and three aggregate summaries.

Usage: python3 parse_tracker.py path/to/job_search_tracker.csv

Writes:
  out/clean_listings.csv   row level, NO company, URL or notes. Git-ignored; import this into Azure SQL.
  summaries/*.csv          aggregates only. These are what the repo publishes.

money(), posted() and contract() follow tools/rank_jobs.py in rahullath/jobby. posted() differs in one
way: it returns None when the notes carry no "Posted <date>", because here a missing date is a finding.
"""
import csv, datetime, re, sys, collections, pathlib

ROOT = pathlib.Path(__file__).parent
FLOOR = 26000  # lowest full-time salary accepted

# ---- from tools/rank_jobs.py -------------------------------------------------
def money(notes):
    m = re.search(r"£\s?([\d,]+(?:\.\d+)?)\s*(?:-|–|to)?\s*£?\s?([\d,]+(?:\.\d+)?)?\s*(/hr|per hour|/day|per day|/yr|per annum|k)?", notes or "")
    if not m:
        return None
    lo = float(m.group(1).replace(",", ""))
    unit = (m.group(3) or "").lower()
    if unit in ("/hr", "per hour") or lo < 60:
        return lo * 1950
    if unit in ("/day", "per day") or 60 <= lo < 1000:
        return lo * 230
    if unit == "k":
        return lo * 1000
    return lo

def posted(r):
    m = re.search(r"Posted (\d{4}-\d{2}-\d{2})", r["notes"])
    return datetime.date.fromisoformat(m.group(1)) if m else None

def contract(r):
    m = re.search(r"CONTRACT: (\w+)( part-time)?", r["notes"])
    if m:
        if m.group(2):
            return "part-time"
        return {"Temporary": "temp", "Contract": "fixed-term", "Permanent": "permanent"}.get(m.group(1), "unknown")
    t = (r["title"] + " " + r["notes"] + " " + r["source"]).lower()
    if "part-time" in t or "part time" in t or "reed-parttime" in t:
        return "part-time"
    if re.search(r"\btemp\b|temporary|interim|maternity|locum|immediate start", t) or "agency/temporary" in t:
        return "temp"
    if re.search(r"fixed.?term|\bftc\b|contract|\d+.month|secondment", t):
        return "fixed-term"
    if "permanent" in t:
        return "permanent"
    return "unknown"
# ------------------------------------------------------------------------------

MONTHS = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}

def closes(notes):
    """(present, date). present counts "Closes ..." in the notes; date is None if the text will not parse."""
    m = re.search(r"\bCloses (\d{4}-\d{2}-\d{2})", notes)
    if m:
        return True, datetime.date.fromisoformat(m.group(1))
    m = re.search(r"\bCloses (\d{1,2})(?:st|nd|rd|th)? ([A-Za-z]{3})[a-z]*(?: (\d{4}))?", notes)
    if m and m.group(2).lower() in MONTHS:
        try:
            return True, datetime.date(int(m.group(3) or 2026), MONTHS[m.group(2).lower()], int(m.group(1)))
        except ValueError:
            return True, None
    return ("Closes " in notes), None

SOURCES = [  # (pattern, name, readable_by_routine)
    (r"adzuna", "adzuna", "yes"), (r"reed", "reed", "yes"), (r"indeed", "indeed", "yes"),
    (r"linkedin", "linkedin", "no"), (r"nhs", "nhs", "yes"), (r"charityjob", "charityjob", "yes"),
    (r"civil", "civil service", "no"), (r"wmjobs", "wmjobs", "no"),
]
def source(s):
    s = s.lower()
    for pat, name, _ in SOURCES:
        if re.search(pat, s):
            return name
    return "portals"

def location_band(loc, notes):
    t = (loc or "").lower()
    if re.search(r"remote|home.?based", t):
        return "remote"
    if re.search(r"wolverhampton|coventry|worcester|telford|stafford|stoke|nuneaton|leamington|warwick|redditch|kidderminster|tamworth|lichfield|hereford|rugby|walsall|dudley|bromsgrove|cannock|burton|leicester|derby|nottingham", t):
        return "far"
    if re.search(r"solihull|edgbaston|smethwick|west bromwich|sandwell|sutton coldfield|selly oak", t):
        return "nearby"
    if "birmingham" in t:
        return "central"
    return "unknown"

FAMILIES = [("data analyst", r"data|bi\b|insight|mi\b|information|reporting|performance|intelligence"),
            ("business analyst", r"business|systems|process"), ("research", r"research|policy|evidence"),
            ("developer", r"developer|engineer|automation|software"), ("finance", r"account|finance|payroll|credit|ledger"),
            ("admin", r"admin|assistant|coordinator|officer|support")]
def family(title):
    t = title.lower()
    for name, pat in FAMILIES:
        if re.search(pat, t):
            return name
    return "other"

def vet(notes):
    fail = re.search(r"VET-FAIL\(\d{4}-\d{2}-\d{2}\): ([^.|]*)", notes)
    ok = re.search(r"VET\(\d{4}-\d{2}-\d{2}\): ok", notes)
    if fail:
        r = fail.group(1).strip().lower()
        if r.startswith("closed"): reason = "closed"
        elif re.match(r"\d+ applicants", r) or "applicants" in r: reason = "too many applicants"
        elif "3+" in r or "years" in r: reason = "3+ or 5+ years asked"
        elif "clearance" in r or "vetting" in r or "sc " in r: reason = "security clearance"
        elif "driving" in r: reason = "driving licence"
        else: reason = "other"
        return "failed", reason
    if ok:
        return "passed", None
    return "unread", None

def gaps(notes):
    m = re.search(r"VET\(\d{4}-\d{2}-\d{2}\): ok[^|]*?\|[^|]*\|\s*gaps: ([^|.]*)", notes)
    return [g.strip() for g in m.group(1).split(",") if g.strip()] if m else []

def main(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    (ROOT / "out").mkdir(exist_ok=True)
    out, src = [], collections.defaultdict(collections.Counter)
    fails, gapc = collections.Counter(), collections.Counter()
    for r in rows:
        n = r["notes"]
        pay = money(n)
        has_close, close_d = closes(n)
        state, reason = vet(n)
        s = source(r["source"])
        out.append(dict(date_found=r["date_found"], source=s, title_family=family(r["title"]),
                        location_band=location_band(r["location"], n), contract=contract(r),
                        pay_annual=round(pay) if pay else "", posted_date=posted(r) or "",
                        closes_date=close_d or "", has_closing=int(has_close),
                        vet_state=state, vet_fail_reason=reason or "", status=r["status"],
                        date_applied=r["date_applied"]))
        c = src[s]
        c["listings"] += 1
        c["read"] += state != "unread"
        c["has_closing_date"] += has_close
        c["has_posted_date"] += "Posted " in n
        c["has_pay"] += pay is not None
        if reason: fails[reason] += 1
        for g in gaps(n): gapc[g] += 1
    with open(ROOT / "out/clean_listings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, out[0].keys()); w.writeheader(); w.writerows(out)

    S = ROOT / "summaries"
    readable = {name: ok for _, name, ok in SOURCES}
    with open(S / "sources.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source", "readable_by_routine", "listings", "read", "has_closing_date", "has_posted_date", "has_pay"])
        for s, c in sorted(src.items(), key=lambda kv: -kv[1]["listings"]):
            w.writerow([s, readable.get(s, "no"), c["listings"], c["read"], c["has_closing_date"], c["has_posted_date"], c["has_pay"]])
    st = collections.Counter(o["status"] for o in out)
    applied = st["applied"] + st["rejected"] + st["interview_invite"]
    funnel = [("found", len(out)), ("read and vetted", sum(o["vet_state"] != "unread" for o in out)),
              ("passed vetting", sum(o["vet_state"] == "passed" for o in out)),
              ("applied", applied), ("interview invite", st["interview_invite"])]
    with open(S / "funnel.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["stage", "count"]); w.writerows(funnel)
    with open(S / "fail_reasons.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["reason", "count"]); w.writerows(fails.most_common())
    with open(S / "gaps.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["gap", "count"]); w.writerows(gapc.most_common(10))
    with open(S / "measures.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["measure", "count"])
        w.writerows([("listings", len(out)), ("never touched", st["new"]),
                     ("with closing date", sum(o["has_closing"] for o in out)),
                     ("with posting date", sum("Posted " in r["notes"] for r in rows)),
                     ("with pay figure", sum(o["pay_annual"] != "" for o in out)),
                     ("below pay floor", sum(o["pay_annual"] != "" and o["pay_annual"] < FLOOR for o in out)),
                     ("rejected", st["rejected"]), ("applied, awaiting", st["applied"])])
    print(open(S / "measures.csv").read()); print(open(S / "funnel.csv").read()); print(open(S / "fail_reasons.csv").read())

if __name__ == "__main__":
    main(sys.argv[1])
