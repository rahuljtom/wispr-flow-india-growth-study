import pandas as pd

from src.transform.reviews import coverage_report


def test_coverage_counts_and_shallow_warning():
    df = pd.DataFrame({
        "app": ["w"] * 3, "store": ["play"] * 3, "country": ["in"] * 3,
        "review_date": pd.to_datetime(["2026-03-01", "2026-03-15", "2026-04-02"], utc=True),
    })
    md = coverage_report(df, min_months=6)
    assert "| w | play | in | 3 |" in md
    assert "2026-03-01" in md and "2026-04-02" in md
    assert "2026-03: 2" in md and "2026-04: 1" in md
    assert "shallow" in md.lower()
