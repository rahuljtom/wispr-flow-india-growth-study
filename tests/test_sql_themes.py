import numpy as np
import pandas as pd
import pytest

from src.analysis.themes import MIN_N, theme_table
from src.analysis.themes_sql import theme_tables
from src.tagging.tagger import TAXONOMY


def fixture(seed=7, n=140):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        store = "playstore" if i < 100 else "appstore"
        country = "ww" if store == "playstore" else ("in" if i % 2 else "us")
        k = int(rng.integers(1, 4))
        themes = list(rng.choice(TAXONOMY[:6], size=k, replace=False))
        rows.append({"review_key": f"r{i}", "rating": int(rng.integers(1, 6)), "store": store,
                     "country": country,
                     "lang_proxy": "en/other" if i % 5 else "roman-Hindi/Devanagari (language proxy)",
                     "review_date": pd.Timestamp("2026-08-01", tz="UTC") + pd.Timedelta(days=int(i * 0.9)),
                     "themes": themes})
    return pd.DataFrame(rows)


def reference(df):
    segs = {"all tagged sample": df, "rating<=2 (low-rated)": df[df["rating"] <= 2]}
    for st, g in df.groupby("store"):
        segs[f"store={st}"] = g
    for lp, g in df.groupby("lang_proxy"):
        segs[lp] = g
    for (st, c), g in df.groupby(["store", "country"]):
        if st == "appstore":
            segs[f"appstore {c} (not comparable windows)"] = g
    overall = pd.concat([theme_table(g, name) for name, g in segs.items()], ignore_index=True)
    month = df["review_date"].dt.strftime("%Y-%m")
    monthly = pd.concat([theme_table(g, f"month={m}") for m, g in df.groupby(month)], ignore_index=True)
    return overall, monthly


@pytest.mark.parametrize("which", [0, 1])
def test_sql_matches_pandas_reference(which):
    df = fixture()
    got = theme_tables(df)[which]
    want = reference(df)[which]
    pd.testing.assert_frame_equal(got.reset_index(drop=True), want.reset_index(drop=True),
                                  check_exact=False, rtol=1e-12, atol=1e-12)


def test_suppression_is_blank_not_zero_and_zero_counts_keep_a_valid_interval():
    df = fixture()
    overall, monthly = theme_tables(df)
    small = monthly[monthly.n_segment < MIN_N]
    assert len(small) > 0 and small["suppressed"].all()
    assert small[["share", "ci_lo", "ci_hi", "mean_rating"]].isna().all().all()
    big = overall[overall.segment == "all tagged sample"].set_index("theme")
    unused = big[big.n_with_theme == 0]
    assert len(unused) > 0
    assert (unused["share"] == 0).all() and (unused["ci_lo"] == 0).all() and (unused["ci_hi"] > 0).all()
    assert unused["mean_rating"].isna().all()


def test_every_theme_in_the_taxonomy_appears_for_every_segment():
    overall, _ = theme_tables(fixture())
    assert overall.groupby("segment").theme.apply(list).map(lambda t: t == TAXONOMY).all()


def test_a_theme_repeated_on_one_review_counts_once():
    df = fixture(n=40)
    df.at[0, "themes"] = [TAXONOMY[0], TAXONOMY[0], TAXONOMY[1]]
    got = theme_tables(df)[0]
    want = reference(df)[0]
    pd.testing.assert_frame_equal(got.reset_index(drop=True), want.reset_index(drop=True),
                                  check_exact=False, rtol=1e-12, atol=1e-12)
