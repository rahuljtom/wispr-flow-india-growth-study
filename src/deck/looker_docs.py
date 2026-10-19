"""Split docs/looker_studio_setup.md into one self-contained guide per dashboard page (docs/looker/).

The master manual stays the single source of truth; this script only slices and wraps it, so the page
guides cannot drift from it. Row and column counts in the data-source tables are read from the CSVs.
"""
import csv
import re
from pathlib import Path

MASTER = Path("docs/looker_studio_setup.md")
OUT = Path("docs/looker")
DASH = Path("outputs/dashboard")

PAGES = [  # (file slug, title, master part heading prefix, sources, status note)
    ("page-01-summary", "Page 1 Summary", "## Part 3.", ["summary"], "See 00-start-here for updating sources after data changes."),
    ("page-02-gap-scenarios", "Page 2 Gap scenarios", "## Part 4.", ["decomposition", "summary"], "See 00-start-here for updating sources after data changes."),
    ("page-03-review-themes", "Page 3 Review themes", "## Part 5.", ["reviews_themes"], "See 00-start-here for updating sources after data changes."),
    ("page-04-review-detail", "Page 4 Review detail", "## Part 6.", ["reviews_themes"], "See 00-start-here for updating sources after data changes."),
    ("page-05-review-months", "Page 5 Review months", "## Part 7.", ["reviews_monthly"], "See 00-start-here for updating sources after data changes."),
    ("page-06-competitors", "Page 6 Competitors", "## Part 8.", ["competitors_matrix", "competitors_evidence"],
     "See 00-start-here for updating sources after data changes."),
    ("page-07-prices", "Page 7 Prices", "## Part 9.", ["pricing_chart", "pricing"],
     "See 00-start-here for updating sources after data changes."),
    ("page-08-offers-checkout", "Page 8 Offers and checkout", "## Part 10.", ["offers"], "See 00-start-here for updating sources after data changes."),
    ("page-09-experiments", "Page 9 Experiments", "## Part 11.", ["experiments_headline"], "See 00-start-here for updating sources after data changes."),
    ("page-10-experiment-grid", "Page 10 Experiment grid (appendix)", "## Part 12.", ["experiments_grid"], "See 00-start-here for updating sources after data changes."),
]
TEXT_NOTES = {
    "competitors_matrix": "The five criterion columns (`android_in_india`, `hinglish_support`, `reach_global_play`, `price_relevance`, `feature_overlap`) must be **Text** (they hold digits and the word `unknown`). `criteria_known` and `known_score_total` are Number.",
    "competitors_evidence": "`score` must be **Text**; everything else Text.",
    "pricing": "`usd_list_price` and `inr_per_month` must be **Text** (they hold numbers, `unknown`, `free (...)` and notes).",
    "pricing_chart": "`inr_per_month` is Number; the rest Text.",
}
COMMON_TROUBLE = """| Symptom | Fix |
|---|---|
| Only one category shows after you clicked a bar | Cross-filtering. Press **Reset** (toolbar), then untick **Apply filter** on every chart (00-start-here, 2.5). |
| Numbers are doubled or too large | Aggregation is Sum. Click the metric pill and choose **Max**. |
| A field is missing in the field list | The chart uses the wrong data source. Change **Setup > Data source**. |
| Chart is empty or shows a red error tile | Check the source name, that every field exists (Resource > Manage added data sources > Refresh fields), and that credentials are Owner's. |
| Text or headers are cut off | Enlarge the element, turn on **Wrap text**, reduce the font to 10. |
| A value you expected is blank | Blank means suppressed or unknown on purpose; never replace it with 0 (set **Missing data** to line breaks, not zero). |
"""


def sections(text):
    parts = re.split(r"(?m)^(?=## )", text)
    return {p.split("\n", 1)[0]: p for p in parts if p.startswith("## ")}


def find(sec, prefix):
    return next(v for k, v in sec.items() if k.startswith(prefix))


def counts(name):
    rows = list(csv.reader((DASH / f"dashboard_{name}.csv").open(newline="", encoding="utf-8")))
    return len(rows) - 1, len(rows[0])


def inline_refs(body, slug):
    body = body.replace("(2.5)", "(00-start-here, section 2.5)")
    body = re.sub(r"STOP AND VERIFY \d+", "STOP AND VERIFY", body)
    banner = ("**Interim banner** `(24, 62, 1232, 26)`: **Add a chart > Table**, source `{src}`, **Dimension** `coverage_note` only, "
              "no metrics. **Style:** **Rows per page** 1; header off; body 14 bold, text `#B00020`, no border. "
              "✅ `INTERIM: 321 of 600 sampled reviews tagged (newest Play reviews only; recency-biased)`.")
    body = body.replace("Banner exactly as in Part 5 step 2 (same table, same position).", banner.format(src="reviews_themes"))
    body = re.sub(r"Banner: same as Part 5 step 2 but source `reviews_monthly` \(dimension `coverage_note`\)\.",
                  banner.format(src="reviews_monthly"), body)
    return body


def page_doc(i, slug, title, part, sources, status, sec, qa_lines, design_lines):
    body = inline_refs(find(sec, part).split("\n", 1)[1], slug)
    src_rows = "\n".join(f"| `{s}` | {counts(s)[0]} | {counts(s)[1]} | {TEXT_NOTES.get(s, 'Numbers are Number, text is Text.')} |"
                         for s in sources)
    prev_l = f"[Previous: {PAGES[i - 1][1]}]({PAGES[i - 1][0]}.md)" if i > 0 else "[Start here](00-start-here.md)"
    next_l = f"[Next: {PAGES[i + 1][1]}]({PAGES[i + 1][0]}.md)" if i < len(PAGES) - 1 else "[Sharing and final QA](11-share-and-final-qa.md)"
    return f"""# {title}: build guide

{prev_l} | [Index](README.md) | {next_l}

Generated from `docs/looker_studio_setup.md` (the master manual); do not edit this file by hand, re-run `python -m src.deck.looker_docs`.

## Before you start (2 minutes)
1. **Complete** [00-start-here.md](00-start-here.md) once: data sources connected and named, canvas 1280 x 800, palette, cross-filtering rule.
2. **Data sources this page uses** (check in Resource > Manage added data sources; expected rows and fields):

| Data source name | Rows | Fields | Type notes |
|---|---|---|---|
{src_rows}

3. **Page furniture** (same on every page): Title text box `(24, 16, 1232, 44)` size 22 bold; subtitle `(24, 62, 1232, 26)` size 12, `#555555`; footer `(24, 764, 1232, 24)` size 10 (copy it from page 1: select, Ctrl/Cmd+C, go to this page, Ctrl/Cmd+V); content from y = 100 to 750; margins 24 px; gap 20 px. Palette: blue `#3B6EA8`, orange `#E07B39`, grey `#8A8A8A`, text `#222222`, banner red `#B00020`.
4. **After creating every chart or table:** select it, **Setup**, scroll to **Chart interactions**, untick **Apply filter**. Set every metric's aggregation to **Max** (click the metric pill).
5. **Position and size:** drag to move and resize. If your editor shows Position/Size fields (some versions, under **Style**), type the numbers given; otherwise place by eye (the canvas is 1280 px wide, so 10% is 128 px) and align neighbours with **Arrange > Align**.

## Build steps
{body.strip()}

## Page checklist (tick before moving on)
{qa_lines}
{design_lines}

## Troubleshooting (this page and general)
{COMMON_TROUBLE}
Page-specific notes are in the steps above. Operations (adding a chart, filter, group, align) are explained in [00-start-here.md](00-start-here.md), section 2.2.

{prev_l} | [Index](README.md) | {next_l}
"""


def main():
    text = MASTER.read_text(encoding="utf-8")
    sec = sections(text)
    OUT.mkdir(parents=True, exist_ok=True)
    part14 = find(sec, "## Part 14.")
    lines = part14.splitlines()
    design = "\n".join(ln for ln in lines if ln.startswith("- [ ]") and any(
        k in ln for k in ("Same palette", "Cross-filtering", "No causal wording")))
    for i, (slug, title, part, sources, status) in enumerate(PAGES):
        n = i + 1
        qa = "\n".join(ln for ln in lines if re.match(rf"- \[ \] {n}:", ln))
        (OUT / f"{slug}.md").write_text(page_doc(i, slug, title, part, sources, status, sec, qa, design), encoding="utf-8")
    start = ["# 00 Start here: data, editor basics and report setup", "",
             "Do this once, before any page guide. Generated from `docs/looker_studio_setup.md`.", ""]
    for key in ("## Updating an existing report", "## Part 1.", "## Part 2."):
        for k, v in sec.items():
            if k.startswith(key):
                start += [v.strip(), ""]
    share = ["# 11 Sharing, access and final QA", "", "Do this after all ten pages are built. Generated from `docs/looker_studio_setup.md`.", ""]
    for key in ("## Part 13.", "## Part 14.", "## Part 15.", "## Part 16."):
        share += [find(sec, key).strip(), ""]
    (OUT / "00-start-here.md").write_text("\n".join(start), encoding="utf-8")
    (OUT / "11-share-and-final-qa.md").write_text("\n".join(share), encoding="utf-8")
    index = ["# Looker Studio dashboard: guides by page", "",
             "Follow in order. Each page guide is self-contained once `00-start-here.md` is done. The master manual is `docs/looker_studio_setup.md`.", "",
             "| Guide | Purpose | Data sources |", "|---|---|---|",
             "| [00 Start here](00-start-here.md) | Data sources, editor basics, canvas, palette, cross-filtering | all 11 |"]
    for slug, title, part, sources, status in PAGES:
        purpose = re.search(r"Purpose: ([^\n]*)", find(sec, part)).group(1)
        index.append(f"| [{title}]({slug}.md) | {purpose[:110]} | {', '.join('`' + s + '`' for s in sources)} |")
    index.append("| [11 Sharing and final QA](11-share-and-final-qa.md) | Viewer access, incognito test, checklist, troubleshooting | n/a |")
    (OUT / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print("wrote", len(list(OUT.glob("*.md"))), "files")


if __name__ == "__main__":
    main()
