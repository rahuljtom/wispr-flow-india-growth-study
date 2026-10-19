import pandas as pd

from src.analysis.competitors import (
    android_score,
    build_matrix,
    parse_inr_range,
    price_score,
    reach_score,
)


def test_reach_score_thresholds():
    assert [reach_score(n) for n in (10_000_000_000, 100_000_000, 99_999_999, 1_000_000, 999_999, 100_000, 99_999, 1_000)] == [
        3, 3, 2, 2, 1, 1, 0, 0]
    assert reach_score(None) is None


def test_parse_inr_range():
    assert parse_inr_range("₹250.00 - ₹950.00 per item") == (250.0, 950.0)
    assert parse_inr_range("₹1,450.00 - ₹42,100.00 per item") == (1450.0, 42100.0)
    assert parse_inr_range("₹50.00 per item") == (50.0, 50.0)
    assert parse_inr_range(None) is None and parse_inr_range("") is None


def test_price_score_rubric_never_compares_unstated_billing_periods():
    assert price_score("free_core") == 3
    assert price_score("free_tier") == 2
    assert price_score("explicit", 320) == 3 and price_score("explicit", 321) == 1
    assert price_score("explicit", None) is None
    assert price_score(None) is None  # Play item ranges have no stated period -> unknown


def test_android_score():
    assert android_score(listed=True, updated_days_ago=30) == 3
    assert android_score(listed=True, updated_days_ago=400) == 2
    assert android_score(listed=False, updated_days_ago=None) is None  # not found is not proof of absence


def test_matrix_has_sourced_scores_and_keeps_unknown():
    m = build_matrix()
    assert {"competitor", "criterion", "score", "source_url", "retrieved_on", "rationale"} <= set(m.columns)
    assert set(m.score) <= {"0", "1", "2", "3", "unknown"}
    sourced = m[m.score != "unknown"]
    assert (sourced.source_url != "").all() and (sourced.rationale != "").all()
    tot = (sourced.assign(s=sourced.score.astype(int)).groupby("competitor").s.agg(["sum", "count"]))
    assert tot.loc["Gboard", "count"] == 5 and tot.loc["Gboard", "sum"] == 13
    assert tot.loc["Superflow", "count"] == 4 and tot.loc["Superflow", "sum"] == 11  # price unknown, not imputed
    sf = m[(m.competitor == "Superflow") & (m.criterion == "price_relevance")].iloc[0]
    assert sf.score == "unknown" and sf.source_url == ""
    assert (m[(m.competitor == "Typeless") & (m.criterion == "price_relevance")].score == "1").all()
    assert "Apple dictation" in set(m.competitor) and (m[m.competitor == "Apple dictation"].score == "unknown").all()
    assert pd.Series(m.criterion.unique()).isin(
        ["android_in_india", "hinglish_support", "reach_global_play", "price_relevance", "feature_overlap"]).all()
