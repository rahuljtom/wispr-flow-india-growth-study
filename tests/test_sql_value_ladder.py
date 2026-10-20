import numpy as np
import pandas as pd

from src.analysis.value_ladder import FX
from src.common.sql import run_sql

PARAMS = {"fx": FX, "india_annual_inr": 320.0, "india_monthly_inr": 400.0}


def reference(df, fx=FX):
    """The previous pandas implementation, kept here as the oracle for the SQL."""
    df = df.copy()
    df["price_inr_per_month"] = pd.to_numeric(df["price_usd_per_month"], errors="coerce") * fx
    india = df["product"].eq("Wispr Flow") & df["plan"].eq("India Pro")
    df.loc[india & df["billing"].eq("annual"), "price_inr_per_month"] = 320.0
    df.loc[india & df["billing"].eq("monthly"), "price_inr_per_month"] = 400.0
    df["price_inr_per_month"] = df["price_inr_per_month"].round(0)
    return df


def test_sql_matches_reference_on_the_committed_pricing_table():
    src = pd.read_csv("data/processed/competitor_pricing.csv")
    out = run_sql("value_ladder.sql", PARAMS, {"pricing": src})
    ref = reference(src)
    assert list(out.columns[: len(src.columns)]) == list(src.columns)
    pd.testing.assert_series_equal(out["price_inr_per_month"], ref["price_inr_per_month"], check_exact=True)
    assert (out["fx_inr_per_usd"] == round(FX, 1)).all()


def test_matches_the_committed_value_ladder_csv():
    src = pd.read_csv("data/processed/competitor_pricing.csv")
    out = run_sql("value_ladder.sql", PARAMS, {"pricing": src})
    committed = pd.read_csv("data/processed/value_ladder.csv")
    pd.testing.assert_frame_equal(out, committed, check_exact=True)


def test_unknown_and_not_applicable_prices_stay_null_not_zero():
    src = pd.DataFrame({"product": ["A", "B", "C"], "plan": ["p"] * 3, "billing": ["annual"] * 3,
                        "price_usd_per_month": ["unknown", "not applicable", "10"]})
    out = run_sql("value_ladder.sql", PARAMS, {"pricing": src})
    assert out["price_inr_per_month"].isna().tolist() == [True, True, False]


def test_ties_round_to_even_like_python():
    src = pd.DataFrame({"product": ["A"] * 3, "plan": ["p"] * 3, "billing": ["annual"] * 3,
                        "price_usd_per_month": ["1.25", "0.75", "2.5"]})
    out = run_sql("value_ladder.sql", {**PARAMS, "fx": 2.0}, {"pricing": src})
    assert out["price_inr_per_month"].tolist() == list(np.round([2.5, 1.5, 5.0], 0))
    assert out["price_inr_per_month"].tolist() == [2.0, 2.0, 5.0]


def test_india_rows_use_the_stated_page_prices_not_fx():
    src = pd.DataFrame({"product": ["Wispr Flow"] * 3, "plan": ["India Pro"] * 3,
                        "billing": ["annual", "monthly", "weekly"],
                        "price_usd_per_month": ["3.4", "unknown", "3.4"]})
    out = run_sql("value_ladder.sql", PARAMS, {"pricing": src})
    assert out["price_inr_per_month"].tolist()[:2] == [320.0, 400.0]
