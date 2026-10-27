"""Run after parse_tracker.py: the published counts must match the baseline in the plan."""
import csv, pathlib
S = pathlib.Path(__file__).parent.parent / "summaries"
m = {r["measure"]: int(r["count"]) for r in csv.DictReader(open(S / "measures.csv"))}
f = {r["stage"]: int(r["count"]) for r in csv.DictReader(open(S / "funnel.csv"))}
want = {"listings": 1908, "never touched": 1609, "with closing date": 35, "with posting date": 882,
        "with pay figure": 1214, "rejected": 31, "applied, awaiting": 56}
for k, v in want.items():
    assert m[k] == v, (k, m[k], v)
assert (f["read and vetted"], f["passed vetting"], f["applied"], f["interview invite"]) == (185, 133, 88, 1), f
print("baseline ok")
