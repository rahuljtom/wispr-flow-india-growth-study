"""Runs the SQL theme tables on the stored interim review snapshot and compares them, byte for byte,
with the committed result files. Skipped when the private review data is absent (a fresh clone)."""
from pathlib import Path

import pytest

TAGS = Path("data/interim/tags/bulk_v3_partial.json")
REVIEWS = Path("data/processed/wispr_reviews.csv")

pytestmark = pytest.mark.skipif(not (TAGS.exists() and REVIEWS.exists()),
                                reason="private review data not present")


def test_sql_output_equals_committed_result_files():
    from src.analysis.run_a1 import load
    from src.analysis.themes_sql import theme_tables

    overall, monthly = theme_tables(load(str(TAGS)))
    assert overall.to_csv(index=False) == Path("data/processed/themes_by_segment.csv").read_text()
    assert monthly.to_csv(index=False) == Path("data/processed/themes_monthly.csv").read_text()


def test_headline_numbers_and_suppressed_july_stay_blank():
    from src.analysis.run_a1 import load
    from src.analysis.themes_sql import theme_tables

    overall, monthly = theme_tables(load(str(TAGS)))
    low = overall[overall.segment == "rating<=2 (low-rated)"].set_index("theme")
    allr = overall[overall.segment == "all tagged sample"].set_index("theme")
    assert int(allr.n_segment.iloc[0]) == 321 and int(low.n_segment.iloc[0]) == 52
    assert round(low.loc["pricing_paywall", "share"] * 100, 1) == 26.9
    assert round(allr.loc["pricing_paywall", "share"] * 100, 1) == 11.2
    july = monthly[monthly.segment == "month=2026-07"]
    assert int(july.n_segment.iloc[0]) == 3 and july["suppressed"].all()
    assert july[["share", "ci_lo", "ci_hi", "mean_rating"]].isna().all().all()
