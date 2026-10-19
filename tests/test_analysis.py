import numpy as np
import pandas as pd
import pytest

from src.analysis.decomposition import adjusted_share, decompose, scenario_grid
from src.analysis.sizing import duration_days, n_per_arm
from src.analysis.trends import did_estimate, pre_stats


def test_decomposition_reproduces_kit_numbers():
    d = decompose(0.14, 0.02, 3.4, 12.0)
    assert d["rev_per_install_index"] == pytest.approx(0.142857, abs=1e-6)
    assert d["price_index"] == pytest.approx(0.28333, abs=1e-4)
    assert d["residual_index"] == pytest.approx(0.50420, abs=1e-4)
    assert d["rev_per_install_index"] == pytest.approx(d["price_index"] * d["residual_index"])


def test_adjusted_share_monotone_and_identity():
    assert adjusted_share(0.02, 0.0) == pytest.approx(0.02)
    vals = [adjusted_share(0.02, m) for m in (0, 0.2, 0.4, 0.6)]
    assert vals == sorted(vals) and vals[-1] == pytest.approx(0.05 / 1.03, rel=1e-6)


def test_scenario_grid_range_and_partial_window():
    g = scenario_grid(0.14, 0.02, 3.4, 12.0, window_days=212, price_start_day=61)
    assert {"missed_share", "price_window_share", "rev_per_install_index", "price_index",
            "residual_index"} <= set(g.columns)
    full = g[(g.missed_share == 0) & (g.price_window_share == 1.0)].iloc[0]
    assert full.price_index == pytest.approx(3.4 / 12)
    part = g[(g.missed_share == 0) & np.isclose(g.price_window_share, 151 / 212)].iloc[0]
    assert part.price_index == pytest.approx((61 / 212) * 1 + (151 / 212) * 3.4 / 12)


def test_sample_size_matches_two_proportion_formula():
    n = n_per_arm(0.30, 0.33)
    hand = (1.959964 + 0.841621) ** 2 * (0.30 * 0.70 + 0.33 * 0.67) / 0.03**2
    assert n == pytest.approx(hand, rel=0.02)  # arcsine vs pooled-variance approximations
    assert 3600 < n < 3900


def test_duration_formula_by_hand():
    # 2n / (1650 * 0.5 * 0.8 * 1.0) with n=3300 -> 6600 / 660 = 10 days
    assert duration_days(3300, 0.5, 0.8, 1.0) == pytest.approx(10.0)
    assert duration_days(3300, 1.0, 1.0, 1.0, daily_installs=1650) == pytest.approx(4.0)


def frame(effect=0.0, n_pre=30, n_post=10, geos=("T", "C1", "C2", "C3"), seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    dates = pd.date_range("2025-09-07", periods=n_pre + n_post, freq="W")
    for g in geos:
        base = 20 + rng.normal(0, 0.5, len(dates))
        post = np.arange(len(dates)) >= n_pre
        y = base + (effect if g == "T" else 0) * post
        for dt, v in zip(dates, y, strict=True):
            rows.append({"date": dt, "geo": g, "target": v, "anchor": 10.0})
    return pd.DataFrame(rows), dates[n_pre]


def test_did_recovers_known_effect():
    df, event = frame(effect=10.0)
    r = did_estimate(df, "T", ["C1", "C2", "C3"], event)
    assert r["status"] == "directional"
    assert r["did_index_points"] == pytest.approx(50.0, abs=5)  # 10 on a base of 20 = +50 index pts
    assert len(r["placebo"]) >= 5
    assert r["rank_among_geos"] == 1


def test_did_not_estimable_on_zero_pre_mean_and_few_controls():
    df, event = frame(effect=10.0)
    df.loc[df.geo == "C1", "target"] = 0.0
    df.loc[df.geo == "C2", "target"] = 0.0
    r = did_estimate(df, "T", ["C1", "C2", "C3"], event)
    assert r["status"] == "not estimable" and "controls" in r["reason"]
    df2, event = frame()
    df2.loc[df2.geo == "T", "target"] = 0.0
    assert did_estimate(df2, "T", ["C1", "C2", "C3"], event)["status"] == "not estimable"


def test_pre_stats_zero_vs_missing_distinct():
    df = pd.DataFrame({"date": pd.date_range("2025-09-07", periods=4, freq="W"),
                       "geo": "T", "target": [0.0, np.nan, 5.0, 5.0], "anchor": 1.0})
    s = pre_stats(df, "T", pd.Timestamp("2025-10-30"))
    assert s["n_zero"] == 1 and s["n_missing"] == 1 and s["pre_mean"] == pytest.approx(10 / 3)


def test_sizing_table_has_follow_up_and_total_days():
    from src.analysis.sizing import sizing_table

    df = sizing_table()
    assert {"follow_up_days", "total_days", "unit_note", "kill_criterion"} <= set(df.columns)
    assert ((df.total_days - df.duration_days - df.follow_up_days).abs() < 0.11).all()
    assert df[df.experiment.str.startswith("E3")].unit_note.str.contains("proxy").all()
    assert not df.kill_criterion.str.contains(r"\.\.\.").any()
