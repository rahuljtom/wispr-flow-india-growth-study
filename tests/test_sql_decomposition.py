import pandas as pd
import pytest

from src.analysis.decomposition import decompose, run_grid, scenario_grid

ARGS = (0.14, 0.02, 3.4, 12.0)
KW = {"window_days": 212, "price_start_day": 61}


def test_sql_grid_matches_reference_implementation():
    sql_grid = run_grid(*ARGS, **KW)
    ref = scenario_grid(*ARGS, **KW)
    assert len(sql_grid) == 12
    pd.testing.assert_frame_equal(sql_grid.reset_index(drop=True), ref.reset_index(drop=True),
                                  check_exact=False, rtol=1e-12, atol=1e-12)


def test_point_estimate_row_and_documented_range():
    g = run_grid(*ARGS, **KW)
    point = g[(g.missed_share == 0) & (g.price_window_share == 1.0)].iloc[0]
    d = decompose(*ARGS)
    for k in ("rev_per_install_index", "price_index", "residual_index"):
        assert point[k] == pytest.approx(d[k], abs=1e-12)
    assert round(point.rev_per_install_index, 3) == 0.143
    assert round(point.price_index, 3) == 0.283
    assert round(point.residual_index, 3) == 0.504
    assert round(g.residual_index.min(), 2) == 0.22 and round(g.residual_index.max(), 2) == 1.22


def test_identity_holds_in_every_scenario():
    g = run_grid(*ARGS, **KW)
    assert (g.price_index * g.residual_index - g.rev_per_install_index).abs().max() < 1e-12
