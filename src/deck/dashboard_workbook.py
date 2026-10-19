"""One Excel workbook, one worksheet per dashboard CSV (for Looker Studio's Microsoft Excel connector).

Why: Looker Studio's File Upload connector keeps all files of a dataset in one schema, so CSVs with
different headers must not share a dataset. A workbook has one worksheet per schema and is uploaded once.
Cells keep the CSV's values: blanks stay empty (suppressed or missing), 'unknown' stays text, and mixed
columns are written as text so a column never mixes numbers and words.
"""
import csv
from pathlib import Path

from openpyxl import Workbook

DIR = Path("outputs/dashboard")
# worksheet name (max 31 characters) -> csv stem
SHEETS = {
    "summary": "dashboard_summary",
    "decomposition": "dashboard_decomposition",
    "reviews_themes": "dashboard_reviews_themes",
    "reviews_monthly": "dashboard_reviews_monthly",
    "competitors_matrix": "dashboard_competitors_matrix",
    "competitors_evidence": "dashboard_competitors_evidence",
    "pricing_chart": "dashboard_pricing_chart",
    "pricing": "dashboard_pricing",
    "offers": "dashboard_offers",
    "experiments_headline": "dashboard_experiments_headline",
    "experiments_grid": "dashboard_experiments_grid",
}
# Columns that mix numbers and words (or hold scores that may be "unknown") are written as text.
TEXT_COLUMNS = {
    "competitors_matrix": ("android_in_india", "hinglish_support", "reach_global_play", "price_relevance",
                           "feature_overlap"),
    "competitors_evidence": ("score",),
    "pricing": ("usd_list_price", "inr_per_month"),
}


def _value(sheet, column, raw):
    if raw == "":
        return None  # blank stays blank
    if column in TEXT_COLUMNS.get(sheet, ()):
        return raw
    try:
        num = float(raw)
    except ValueError:
        return raw
    return int(num) if num.is_integer() and "." not in raw else num


def build(path=DIR / "wispr_dashboard_data.xlsx"):
    wb = Workbook()
    wb.remove(wb.active)
    for sheet, stem in SHEETS.items():
        with (DIR / f"{stem}.csv").open(newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        ws = wb.create_sheet(sheet)
        ws.append(rows[0])
        for r in rows[1:]:
            ws.append([_value(sheet, col, v) for col, v in zip(rows[0], r, strict=True)])
        ws.freeze_panes = "A2"
    wb.properties.creator = "wispr-flow-analytics"
    wb.properties.title = "Wispr Flow India diagnostic: dashboard data (one worksheet per table)"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return Path(path)


if __name__ == "__main__":
    print(build())
