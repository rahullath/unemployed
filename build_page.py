"""Build docs/index.html from summaries/*.csv. Plain HTML and CSS, no JavaScript, no external requests.

Design: the Weltschmerz design system (tokens, UnitChart rules). One mark = UNIT listings. A part mark is
clipped, never shrunk. Run parse_tracker.py first."""
import csv, html, math, pathlib

ROOT = pathlib.Path(__file__).parent
UNIT = 50
INK = "var(--spine-research)"  # one strand for the whole page

def rd(name):
    return list(csv.DictReader(open(ROOT / "summaries" / name, encoding="utf-8")))

def e(s):
    return html.escape(str(s))

def marks(count):
    n = count / UNIT
    full, part = int(math.floor(n)), n - math.floor(n)
    cells = ['<i class="m f"></i>'] * full
    if part > 0:
        cells.append(f'<i class="m p"><b style="width:{part*100:.1f}%"></b></i>')
    groups = [cells[i:i + 5] for i in range(0, len(cells), 5)]
    return "".join(f'<span class="g">{"".join(g)}</span>' for g in groups)

def chart(rows, key):
    out = [f'<div class="chart" role="group" aria-label="{e(key)}">']
    for label, count, readout in rows:
        out.append(f'<div class="row"><span class="lab">{e(label)}</span>'
                   f'<span class="run" aria-hidden="true">{marks(count)}</span>'
                   f'<span class="readout">{e(readout)}</span></div>')
    out.append(f'<p class="key">Each mark = {UNIT} listings. A part mark is clipped, not shrunk.</p></div>')
    return "".join(out)

def table(head, rows):
    h = "".join(f"<th>{e(x)}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{e(x)}</td>" for x in r) + "</tr>" for r in rows)
    return f'<details><summary>Exact counts</summary><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></details>'

M = {r["measure"]: int(r["count"]) for r in rd("measures.csv")}
F = {r["stage"]: int(r["count"]) for r in rd("funnel.csv")}
S = rd("sources.csv")
R = rd("fail_reasons.csv")
G = rd("gaps.csv")
total = M["listings"]
whole, part = divmod(total, UNIT)

src_rows = [(r["source"], int(r["listings"]), f'{r["listings"]} listed, {r["has_closing_date"]} with a closing date') for r in S]
fun_rows = [(k, v, str(v)) for k, v in F.items()]
fail_rows = [(r["reason"], int(r["count"]), r["count"]) for r in R]
gap_rows = [(r["gap"], int(r["count"]), r["count"]) for r in G]

CSS = """
:root{--paper:#f4f0e6;--raised:#fffdf8;--sunken:#e8e2d4;--ink:#141210;--muted:#55504a;--faint:#78726a;--rule:#d3cbb9;--bold:#272320;--focus:#0b4fc4;--spine-research:#2d6630;--spine-fragility:#bf2a14;--on-ink:#fffdf8}
@media (prefers-color-scheme:dark){:root{--paper:#1a1613;--raised:#241f1a;--sunken:#110e0b;--ink:#f5f0e6;--muted:#b0a899;--faint:#908878;--rule:#3b342c;--bold:#cfc8b8;--focus:#8fb8ff;--spine-research:#8bd46a;--spine-fragility:#ff8065;--on-ink:#1a1613}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/25px "Hanken Grotesk",system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:0 24px 96px}section{margin-top:64px}
h1,h2{font-family:Archivo,"Helvetica Neue",Helvetica,sans-serif;font-weight:700;margin:0;letter-spacing:-.02em}
h1{font-size:clamp(32px,6vw,48px);line-height:1.04;margin-top:16px}h2{font-size:30px;line-height:33px;border-top:2px solid var(--bold);padding-top:16px}
.key,.readout,td,th,.fig{font-family:"Spline Sans Mono",ui-monospace,SFMono-Regular,monospace}
.key{font-size:12px;line-height:14px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.lede{font-size:19px;line-height:28px;max-width:66ch}.cap{font-size:13px;line-height:18px;font-weight:500;color:var(--muted);max-width:70ch}
header{padding-top:24px}a{color:var(--ink)}
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule);margin-top:32px}
.strip div{background:var(--sunken);padding:16px}.fig{display:block;font-size:30px;line-height:32px;font-weight:600}
.chart{margin-top:24px}.row{display:grid;grid-template-columns:128px 1fr;gap:4px 8px;padding:5px 0;border-top:1px solid var(--rule)}
.lab{font-weight:600}.run{display:flex;flex-wrap:wrap;gap:3px 11px;align-items:center;min-height:22px}.g{display:inline-flex;gap:3px}
.readout{grid-column:2;font-size:13px;line-height:18px;color:var(--muted)}
.m{display:inline-block;width:15px;height:15px;background:var(--spine-research)}.p{background:none;outline:1px solid var(--faint);outline-offset:-1px;position:relative}
.p b{position:absolute;left:0;top:0;bottom:0;background:var(--spine-research)}
@media(min-width:720px){.m{width:22px;height:22px}.row{grid-template-columns:128px 1fr auto}.readout{grid-column:auto;align-self:center;text-align:right;min-width:12ch}}
details{margin-top:12px}summary{cursor:pointer;font-size:14px}summary:focus-visible,a:focus-visible{outline:2px solid var(--focus);outline-offset:4px}
table{border-collapse:collapse;margin-top:8px;font-size:13px;width:100%}th,td{text-align:left;padding:6px 12px 6px 0;border-top:1px solid var(--rule)}th{background:var(--sunken);padding-left:8px}
.note{margin-top:32px;padding:16px;background:var(--raised);border:1px solid var(--rule);border-left:5px solid var(--spine-fragility);border-radius:4px}.note ul{margin:8px 0 0;padding-left:20px}
footer{margin-top:64px;border-top:2px solid var(--bold);padding-top:16px}
"""

body = f"""<main><header><p class="key">Weltschmerz build nine</p>
<h1>A job board promises to tell you what is open and whether you fit. Over five weeks it handed this search {total:,} listings.</h1>
<p class="lede">It showed a closing date for {M['with closing date']} of them, an advert we could actually read for {F['read and vetted']}, and led to {F['interview invite']} interview.</p>
<div class="strip">
<div><span class="fig">{total:,}</span><span class="key">listings found</span></div>
<div><span class="fig">{M['with closing date']}</span><span class="key">with a closing date</span></div>
<div><span class="fig">{F['read and vetted']}</span><span class="key">adverts read and vetted</span></div>
<div><span class="fig">{F['interview invite']}</span><span class="key">interview</span></div></div>
<p class="cap">Source: one job search tracker, 22 September to 27 October 2026. Counted by parse_tracker.py in this repository. The whole board is {whole} marks and a part mark of {part} listings.</p></header>
<section><h2>What the board says and what we could read</h2>
<p class="lede">Listings by source. Reed and Adzuna supply most of them and publish a posting date; almost none of any source gives a closing date.</p>
{chart(src_rows, "Listings by source")}{table(["source","readable by routine","listings","read","closing date","posting date","pay figure"],[[r["source"],r["readable_by_routine"],r["listings"],r["read"],r["has_closing_date"],r["has_posted_date"],r["has_pay"]] for r in S])}
<p class="cap">Method: source names in the tracker are merged (for example jobspy(linkedin) and linkedin). A closing date counts when the tracker notes contain one; {M['with posting date']:,} listings carry a posting date and {M['with pay figure']:,} a pay figure.</p></section>
<section><h2>The funnel</h2>
<p class="lede">Of {total:,} listings, {M['never touched']:,} were never opened. {F['applied']} became applications.</p>
{chart(fun_rows, "Funnel from found to interview")}{table(["stage","count"],[[k,v] for k,v in F.items()])}
<p class="cap">Method: applied counts statuses applied ({M['applied, awaiting']}), rejected ({M['rejected']}) and interview invite (1). Read and vetted counts listings with a VET or VET-FAIL line in the notes.</p></section>
<section><h2>Why adverts fail</h2>
<p class="lede">{sum(int(r['count']) for r in R)} adverts failed vetting. The advert had already closed in {next((r['count'] for r in R if r['reason']=='closed'),0)} of them.</p>
{chart(fail_rows, "Reasons an advert failed vetting")}{table(["reason","count"],[[r["reason"],r["count"]] for r in R])}
<p class="lede">Tools the adverts ask for that the CV does not carry, from the gaps recorded while vetting.</p>
{chart(gap_rows, "Tools adverts asked for, recorded as gaps")}{table(["tool","count"],[[r["gap"],r["count"]] for r in G])}
<p class="cap">Method: reasons are grouped from the VET-FAIL text. "3+ or 5+ years asked" joins two wordings. Gaps are the tools named after "gaps:" in vetting notes.</p></section>
<aside class="note"><span class="key">Limit to respect</span><ul>
<li>One candidate, one region, five weeks. This is not a market study.</li>
<li>A missing closing date means we could not read one, not that the board had none.</li>
<li>Aggregates only. No company names, no links, no notes are published.</li></ul></aside>
<footer><p class="cap">Code: MIT. Figures and text: CC BY 4.0. Page weight: PAGE_WEIGHT. No scripts, no external requests. Built with the <a href="https://weltschmerz-labs.vercel.app">Weltschmerz</a> design system. Fonts fall back to system faces.</p></footer></main>"""

page = f'<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>The job board, counted</title><meta name="description" content="{total:,} job listings, {M["with closing date"]} closing dates, {F["read and vetted"]} adverts read, {F["interview invite"]} interview. Counted in marks."><style>{CSS}</style></head><body>{body}</body></html>'
size = len(page.encode()) + 12
page = page.replace("PAGE_WEIGHT", f"{size/1024:.1f} KB")
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs" / "index.html").write_text(page, encoding="utf-8")
print("docs/index.html", size, "bytes")
