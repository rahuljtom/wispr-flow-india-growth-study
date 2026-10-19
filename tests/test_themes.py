import pandas as pd
import pytest

from src.analysis.themes import MIN_N, theme_table, wilson


def test_wilson_reference_values():
    lo, hi = wilson(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-3) and hi == pytest.approx(0.7634, abs=1e-3)
    lo, hi = wilson(0, 40)
    assert lo == 0.0 and hi == pytest.approx(0.0877, abs=1e-3)
    assert wilson(0, 0) == (None, None)


def frame(n):
    return pd.DataFrame({
        "review_key": [f"k{i}" for i in range(n)],
        "rating": [5 if i % 2 else 1 for i in range(n)],
        "themes": [["ui_ux"] if i < n // 4 else ["other"] for i in range(n)],
    })


def test_theme_table_share_ci_and_suppression():
    t = theme_table(frame(100), segment="all").set_index("theme")
    assert t.loc["ui_ux", "n_with_theme"] == 25 and t.loc["ui_ux", "share"] == pytest.approx(0.25)
    assert t.loc["ui_ux", "n_segment"] == 100 and not t.loc["ui_ux", "suppressed"]
    assert t.loc["ui_ux", "ci_lo"] < 0.25 < t.loc["ui_ux", "ci_hi"]
    small = theme_table(frame(MIN_N - 1), segment="tiny")
    assert small["suppressed"].all() and small["share"].isna().all() and small["mean_rating"].isna().all()


def test_multi_theme_counts_each_theme():
    df = frame(40)
    df.at[0, "themes"] = ["ui_ux", "other"]
    t = theme_table(df, "all").set_index("theme")
    assert t.loc["ui_ux", "n_with_theme"] == 10 and t.loc["other", "n_with_theme"] == 31
