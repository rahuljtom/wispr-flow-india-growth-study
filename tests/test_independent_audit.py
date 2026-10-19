"""Independent recomputation (different code paths) of figures shown in the deck and dashboard."""
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm
from statsmodels.stats.proportion import proportion_confint

DASH = Path("outputs/dashboard")


def load(path):
    return json.loads(Path(path).read_text())


def have(*paths):
    return all(Path(p).exists() for p in paths)


@pytest.mark.skipif(not have("data/interim/tags/bulk_v3_partial.json", "data/processed/wispr_reviews.csv",
                             "data/private/gold_split_key.csv", "data/interim/bulk_sample_ids.csv"),
                    reason="review text, tags and gold files are private and not distributed")
def test_theme_table_matches_independent_wilson_and_counts():
    tags = load("data/interim/tags/bulk_v3_partial.json")
    rv = pd.read_csv("data/processed/wispr_reviews.csv").set_index("review_key")
    gold = set(pd.read_csv("data/private/gold_split_key.csv").review_key)
    ids = set(pd.read_csv("data/interim/bulk_sample_ids.csv").review_key)
    assert not (set(tags) & gold) and set(tags) <= ids and len(ids) == 600  # gold excluded, sample fixed
    df = rv.loc[list(tags)].copy()
    df["themes"] = [tags[k]["themes"] for k in df.index]
    n, low = len(df), df[df.rating <= 2]
    for r in pd.read_csv(DASH / "dashboard_reviews_themes.csv").itertuples():
        th = r.theme_label.replace(" ", "_")
        k = sum(th in t for t in df.themes)
        lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
        assert (k, round(k / n * 100, 1), round(lo * 100, 1), round(hi * 100, 1)) == (
            r.n_with_theme_all, r.share_all_pct, r.ci_lo_all_pct, r.ci_hi_all_pct)
        kl = sum(th in t for t in low.themes)
        l2, h2 = proportion_confint(kl, len(low), alpha=0.05, method="wilson")
        assert (kl, round(l2 * 100, 1), round(h2 * 100, 1)) == (r.n_with_theme_low, r.ci_lo_low_pct, r.ci_hi_low_pct)
    assert (n, len(low)) == (321, 52)
    months = df.review_date.str[:7].value_counts().sort_index().to_dict()
    got = pd.read_csv(DASH / "dashboard_reviews_monthly.csv").set_index("month_label").reviews.to_dict()
    assert months == got


@pytest.mark.skipif(not have("data/private/gold_labels.csv", "data/interim/tags/test_v3.json"), reason="private data")
def test_test_split_metrics_recomputed_independently():
    gl = pd.read_csv("data/private/gold_labels.csv", dtype=str, keep_default_na=False).set_index("gold_id")
    key = pd.read_csv("data/private/gold_split_key.csv").set_index("gold_id")
    tags = load("data/interim/tags/test_v3.json")
    tp = fp = fn = 0
    pairs = []
    for gid in key[key.split == "test"].index:
        g = {x.strip().lower() for x in gl.loc[gid, "themes"].replace(";", ",").split(",") if x.strip()}
        p = set(tags[key.loc[gid, "review_key"]]["themes"])
        tp, fp, fn = tp + len(g & p), fp + len(p - g), fn + len(g - p)
        pairs.append((gl.loc[gid, "sentiment"].lower(), tags[key.loc[gid, "review_key"]]["sentiment"]))
    f1 = 2 * tp / (2 * tp + fp + fn)
    po = np.mean([a == b for a, b in pairs])
    labs = {x for p in pairs for x in p}
    pe = sum(np.mean([a == label for a, _ in pairs]) * np.mean([b == label for _, b in pairs]) for label in labs)
    stored = load("data/interim/eval_test.json")
    assert f1 == pytest.approx(stored["micro_f1"]) and (po - pe) / (1 - pe) == pytest.approx(stored["sentiment_kappa"])


def test_experiment_sample_sizes_agree_with_pooled_variance_formula():
    z = norm.ppf(0.975) + norm.ppf(0.8)
    e = pd.read_csv("data/processed/experiment_sizing.csv")
    worst = 0.0
    for r in e.drop_duplicates(["experiment", "baseline", "mde_abs"]).itertuples():
        p1, p2 = r.baseline, r.baseline + r.mde_abs
        pooled = z * z * (p1 * (1 - p1) + p2 * (1 - p2)) / (p2 - p1) ** 2
        worst = max(worst, abs(r.n_per_arm - pooled) / pooled)
    assert worst < 0.07  # arcsine (statsmodels) vs pooled-variance: method gap stays under 7%
    calc = 2 * e.n_per_arm / (1650 * e.android_share * e.eligible_share * e.exposed_share)
    assert (calc - e.duration_days).abs().max() < 0.06
    assert ((e.total_days - e.duration_days - e.follow_up_days).abs() < 0.11).all()


def test_competitor_scores_recomputed_from_play_facts_and_never_compare_unstated_periods():
    st = pd.read_csv("data/interim/competitor_play_stats.csv").set_index("name")
    m = pd.read_csv("data/processed/competitor_matrix.csv", dtype=str, keep_default_na=False)
    score = {(r.competitor, r.criterion): r.score for r in m.itertuples()}
    for name, r in st.iterrows():
        if (name, "reach_global_play") not in score:
            continue
        n = r.min_installs
        want = "3" if n >= 100e6 else "2" if n >= 1e6 else "1" if n >= 100e3 else "0"
        assert score[(name, "reach_global_play")] == want, name
    # Play item ranges have no billing period: no app may score price from them
    for name in ("Superflow", "Bobble AI Keyboard", "SoundType AI"):
        assert score[(name, "price_relevance")] == "unknown", name
    assert score[("Gboard", "price_relevance")] == "3"
    sourced = m[m.score != "unknown"]
    assert (sourced.source_url != "").all() and (sourced.retrieved_on != "").all()
    unknown = m[m.score == "unknown"]
    assert (unknown.source_url == "").all()  # no source claimed for a missing score


def test_ranking_lets_unknowns_widen_the_range_instead_of_imputing_zero():
    r = pd.read_csv("data/processed/competitor_ranking.csv").set_index("competitor")
    assert r.loc["Superflow", "total"] == 11 and r.loc["Superflow", "max_possible"] == 14
    assert r.loc["Gboard", "total"] == 13 and r.loc["Gboard", "unknown"] == 0
    assert r.loc["Superflow", "min_possible"] > r.loc["Typeless", "max_possible"]  # leads dedicated dictation apps
    assert r.loc["Apple dictation", "max_possible"] == 15 and r.loc["Apple dictation", "total"] == 0


def test_pricing_table_does_not_invent_periods_or_free_prices():
    rows = list(csv.DictReader((DASH / "dashboard_pricing.csv").open()))
    play = [r for r in rows if r["plan"] == "Play in-app items"]
    assert play and all("billing period not stated" in r["inr_per_month"] and r["billing"] == "unknown" for r in play)
    free = [r for r in rows if r["inr_per_month"].startswith("free")]
    assert {r["product"] for r in free} == {"Gboard", "Hindi Voice Typing (HinKhoj)"}
    chart = list(csv.DictReader((DASH / "dashboard_pricing_chart.csv").open()))
    assert all(r["billing"] in ("annual", "monthly") for r in chart)  # only stated periods are charted
