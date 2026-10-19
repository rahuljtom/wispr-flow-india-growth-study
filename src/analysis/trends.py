"""A3: Karnataka vs control states (rules 3-5). Directional diagnostics only, never causal.

Each geo is expressed as an index of its own pre-period mean (=100). A geo is usable only if its
pre-period has a positive mean, enough non-zero weeks and few missing weeks; otherwise it is
"not estimable" (rule 4). A difference-in-differences needs the treated geo and at least two usable
controls.
"""
import numpy as np
import pandas as pd

MIN_NONZERO_PRE_WEEKS = 10
MAX_MISSING_SHARE = 0.1
MIN_CONTROLS = 2


def pre_stats(df, geo, event):
    s = df[(df.geo == geo) & (df.date < event)]["target"]
    return {"geo": geo, "n_pre": len(s), "n_zero": int((s == 0).sum()), "n_missing": int(s.isna().sum()),
            "n_nonzero": int((s > 0).sum()), "pre_mean": float(s.mean()) if s.notna().any() else np.nan}


def usable(stats):
    return bool(stats["pre_mean"] > 0 and stats["n_nonzero"] >= MIN_NONZERO_PRE_WEEKS
                and stats["n_missing"] <= MAX_MISSING_SHARE * max(stats["n_pre"], 1))


def index_series(df, geo, event):
    g = df[df.geo == geo].set_index("date")["target"].sort_index()
    return g / pre_stats(df, geo, event)["pre_mean"] * 100


def _did(df, treated, controls, event, window_start=None):
    t = index_series(df, treated, event)
    c = pd.concat([index_series(df, g, event) for g in controls], axis=1).mean(axis=1)
    diff = (t - c).dropna()
    if window_start is not None:
        diff = diff[diff.index >= window_start]
    pre, post = diff[diff.index < event], diff[diff.index >= event]
    return float(post.mean() - pre.mean()), diff


def did_estimate(df, treated, controls, event, n_placebo=5):
    event = pd.Timestamp(event)
    geos = [treated, *controls]
    stats = {g: pre_stats(df, g, event) for g in geos}
    ok = {g: usable(s) for g, s in stats.items()}
    out = {"event_date": str(event.date()), "treated": treated, "pre_stats": stats,
           "usable": ok, "label": "directional diagnostic, not causal"}
    good_controls = [g for g in controls if ok[g]]
    if not ok[treated]:
        return {**out, "status": "not estimable",
                "reason": "treated geo pre-period is zero or too sparse"}
    if len(good_controls) < MIN_CONTROLS:
        return {**out, "status": "not estimable",
                "reason": f"fewer than {MIN_CONTROLS} usable controls ({len(good_controls)})"}
    did, diff = _did(df, treated, good_controls, event)
    pre = diff[diff.index < event]
    slope = float(np.polyfit(np.arange(len(pre)), pre.values, 1)[0]) if len(pre) > 2 else np.nan
    # placebo: pretend the event happened earlier, using pre-period weeks only
    pre_dates = pre.index
    cands = pre_dates[MIN_NONZERO_PRE_WEEKS + 2:len(pre_dates) - 4]
    picks = cands[np.linspace(0, len(cands) - 1, n_placebo).round().astype(int)] if len(cands) else []
    placebo = []
    for d in picks:
        sub = df[df.date < event]
        base = pre_stats(sub, treated, d)
        if usable(base):
            val, _ = _did(sub, treated, good_controls, d)
            placebo.append({"date": str(pd.Timestamp(d).date()), "did_index_points": val})
    # rank: each usable geo treated against the others
    pool = [g for g in geos if ok[g]]
    effects = {}
    for g in pool:
        others = [x for x in pool if x != g]
        if len(others) >= MIN_CONTROLS:
            effects[g] = _did(df, g, others, event)[0]
    rank = (sorted(effects, key=effects.get, reverse=True).index(treated) + 1
            if treated in effects else None)
    return {**out, "status": "directional", "did_index_points": did,
            "pre_trend_slope_index_points_per_week": slope, "placebo": placebo,
            "rank_among_geos": rank, "n_geos_ranked": len(effects), "controls_used": good_controls}
