"""Dashboard tables for Looker Studio (aggregates only: no review text or identifiers).

Design rules (see docs/looker_studio_setup.md):
- every derived field is computed here, so the report needs no calculated fields or chart filters;
- one table per visual purpose, readable text labels, percentages already in percent units (*_pct);
- suppressed values (fewer than 30 reviews) stay blank and carry a text label; unknown scores stay the
  word "unknown"; nothing is converted to zero.
dashboard_trends is omitted because the Karnataka difference-in-differences is not estimable.
"""
import json
from pathlib import Path

import pandas as pd

from src.analysis.sizing import EXPERIMENTS, HEADLINE
from src.common.ledger import read_ledger

OUT = Path("outputs/dashboard")
CRITERIA = {"android_in_india": "Android in India", "hinglish_support": "Hinglish support",
            "reach_global_play": "Reach (global Play installs)", "price_relevance": "Price relevance",
            "feature_overlap": "Feature overlap"}
TAGGER = "Frozen prompt v3, Gemini Flash-Lite; directional; one-labeller gold set"


def write(df, name):
    df.to_csv(OUT / f"dashboard_{name}.csv", index=False)


def ledger_value(cid):
    return float(next(r["value"] for r in read_ledger() if r["claim_id"] == cid))


def coverage_note(cov):
    if cov["complete"]:
        return "Complete sample"
    return (f"INTERIM: {cov['tagged']} of {cov['sample']} sampled reviews tagged "
            "(newest Play reviews only; recency-biased)")


def summary(dec):
    return pd.DataFrame({
        "measure": ["Installs from India", "In-app purchase revenue from India"],
        "share_pct": [ledger_value("R-002"), ledger_value("R-003")],
        "rev_per_install_index": ledger_value("R-011"), "price_index": ledger_value("R-012"),
        "residual_index": ledger_value("R-013"),
        "residual_min": round(dec["residual_index"].min(), 3), "residual_max": round(dec["residual_index"].max(), 3),
        "window": "Oct 2025 to Apr 2026",
        "source": "Sensor Tower via TechCrunch; in-app purchases only; indices are scenarios, not causal",
    })


def decomposition(dec):
    d = pd.DataFrame({
        "scenario": [f"{round(m * 100)}% missed | {round(w * 100)}% of window"
                     for m, w in zip(dec.missed_share, dec.price_window_share, strict=True)],
        "missed_revenue_pct": (dec.missed_share * 100).round(0).astype(int),
        "window_at_india_price_pct": (dec.price_window_share * 100).round(0).astype(int),
        "rev_per_install": dec.rev_per_install_index.round(3), "price_index": dec.price_index.round(3),
        "residual": dec.residual_index.round(3)})
    return d.sort_values(["missed_revenue_pct", "window_at_india_price_pct"]).reset_index(drop=True)


def _theme_cols(seg, suffix):
    seg = seg.set_index("theme")
    sup = bool(seg["suppressed"].astype(str).str.lower().eq("true").any())
    out = pd.DataFrame(index=seg.index)
    out[f"n_with_theme_{suffix}"] = seg["n_with_theme"].astype(int)
    for col, name in (("share", "share"), ("ci_lo", "ci_lo"), ("ci_hi", "ci_hi")):
        out[f"{name}_{suffix}_pct"] = (seg[col] * 100).round(1)
    out[f"share_{suffix}_label"] = [
        "suppressed (n<30)" if sup or pd.isna(r.share) else f"{r.share * 100:.1f}% ({r.ci_lo * 100:.1f}-{r.ci_hi * 100:.1f})"
        for r in seg.itertuples()]
    return out


def reviews_themes(th, cov):
    allseg = th[th.segment == "all tagged sample"]
    low = th[th.segment == "rating<=2 (low-rated)"]
    a, b = _theme_cols(allseg, "all"), _theme_cols(low, "low")
    out = a.join(b)
    out["mean_rating_all"] = allseg.set_index("theme")["mean_rating"].round(2)
    out = out.sort_values("share_all_pct", ascending=False)
    out.insert(0, "rank", range(1, len(out) + 1))
    out.insert(1, "theme_label", [t.replace("_", " ") for t in out.index])
    out["reviews_all"] = int(allseg.n_segment.iloc[0])
    out["reviews_low_rated"] = int(low.n_segment.iloc[0])
    out["reviews_selected"] = cov["sample"]
    out["coverage_note"] = coverage_note(cov)
    out["tagger_note"] = TAGGER
    return out.reset_index(drop=True)


def reviews_monthly(mo, cov):
    keep = {"praise_productivity": "praise_productivity_pct", "accuracy_general": "accuracy_general_pct",
            "pricing_paywall": "pricing_paywall_pct"}
    rows = []
    for seg, g in mo.groupby("segment"):
        g = g.set_index("theme")
        sup = str(g["suppressed"].iloc[0]).lower() == "true"
        row = {"month_label": seg.replace("month=", ""), "reviews": int(g["n_segment"].iloc[0]),
               "status": "suppressed (n<30)" if sup else "shown"}
        for theme, col in keep.items():
            row[col] = None if sup else round(g.loc[theme, "share"] * 100, 1)
        row["coverage_note"] = coverage_note(cov)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("month_label").reset_index(drop=True)


def competitors(cm):
    wide = cm.pivot(index="competitor", columns="criterion", values="score")[list(CRITERIA)]
    out = wide.copy()
    out["criteria_known"] = wide.apply(lambda r: int((r != "unknown").sum()), axis=1)
    out["known_score_total"] = wide.apply(lambda r: int(sum(int(v) for v in r if v != "unknown")), axis=1)
    out = out.sort_values(["criteria_known", "known_score_total"], ascending=False).reset_index()
    out.columns = ["competitor", *CRITERIA, "criteria_known", "known_score_total"]
    ev = cm[cm.score != "unknown"].copy()
    ev["criterion"] = ev.criterion.map(CRITERIA)
    ev = ev[["competitor", "criterion", "score", "rationale", "source_url", "retrieved_on"]]
    ev = ev.sort_values(["competitor", "criterion"]).reset_index(drop=True)
    return out, ev


def pricing(vl):
    vl = vl.copy()
    vl["price_note"] = vl.get("price_note", "")
    vl["inr"] = pd.to_numeric(vl.price_inr_per_month, errors="coerce")
    chart = vl[vl.inr.notna()].copy()
    chart["label"] = (chart["product"] + " " + chart["plan"] + " (billed "
                      + chart["billing"].map({"annual": "annually", "monthly": "monthly"}) + ")")
    chart = chart.sort_values("inr")[["label", "inr", "product", "billing", "source_url"]]
    chart.columns = ["label", "inr_per_month", "product", "billing", "source_url"]
    chart["group"] = ["Wispr Flow" if p == "Wispr Flow" else "Other" for p in chart["product"]]
    chart["inr_per_month"] = chart["inr_per_month"].round(0).astype(int)
    table = pd.DataFrame({
        "product": vl["product"], "plan": vl["plan"], "billing": vl["billing"],
        "usd_list_price": vl["price_usd_per_month"].astype(str),
        "inr_per_month": [note if isinstance(note, str) and note else ("unknown" if pd.isna(v) else str(round(v)))
                          for note, v in zip(vl["price_note"], vl["inr"], strict=True)],
        "free_tier": vl["free_tier"], "source_url": vl["source_url"], "retrieved_on": vl["retrieved_on"],
        "fx_note": "USD prices at 94.1 INR per USD (implied by TechCrunch); India rows are INR list prices"})
    return chart.reset_index(drop=True), table.reset_index(drop=True)


def offers(of):
    out = pd.DataFrame({
        "offer": of.offer, "what_is_offered": of.benefit_stated, "duration": of.duration_stated,
        "eligibility": of.eligibility_stated, "restrictions": of.restrictions_stated,
        "platform": of.platform_stated, "android_specific": of.android_specific,
        "redeemable_today": of.currently_redeemable.fillna("n/a"), "evidence": of.evidence_type,
        "status": of.status, "source_url": of.source_url})
    return out.fillna("not stated")


def experiments(sz):
    short = {k[:2]: v["short_name"] for k, v in EXPERIMENTS.items()}
    full = {k[:2]: k for k in EXPERIMENTS}
    sz = sz.copy()
    sz["code"] = sz.experiment.str[:2]
    grid = pd.DataFrame({
        "experiment": sz.code.map(short), "baseline_pct": (sz.baseline * 100).round(1),
        "mde_points": (sz.mde_abs * 100).round(1), "android_share_pct": (sz.android_share * 100).round(0).astype(int),
        "eligible_share_pct": (sz.eligible_share * 100).round(0).astype(int),
        "exposed_share_pct": (sz.exposed_share * 100).round(0).astype(int), "n_per_arm": sz.n_per_arm,
        "enrolment_days": sz.duration_days, "follow_up_days": sz.follow_up_days, "total_days": sz.total_days})
    rows = []
    for code, (base, mde) in HEADLINE.items():
        cell = sz[(sz.code == code) & (sz.baseline == base) & (sz.mde_abs == mde)]
        default = cell[(cell.eligible_share == 0.8) & (cell.exposed_share == 1.0)
                       & (cell.android_share == (1.0 if code == "E3" else 0.5))].iloc[0]
        e = EXPERIMENTS[full[code]]
        rows.append({
            "experiment": e["short_name"], "primary_metric": e["metric"], "baseline_pct": round(base * 100, 1),
            "mde_points": round(mde * 100, 1), "n_per_arm": int(default.n_per_arm),
            "enrolment_days_default": default.duration_days, "follow_up_days": int(default.follow_up_days),
            "total_days_default": default.total_days, "total_days_min": cell.total_days.min(),
            "total_days_max": cell.total_days.max(), "guardrails": e["guardrails"], "decision_rule": e["short_rule"],
            "caveat": ("Illustrative baseline and MDE (assumptions); guardrail limits need internal baselines"
                       + ("; " + e["unit_note"] if e["unit_note"] else ""))})
    return pd.DataFrame(rows), grid.reset_index(drop=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("dashboard_*.csv"):
        old.unlink()
    cov = json.loads(Path("data/processed/a1_coverage.json").read_text())
    dec = pd.read_csv("data/processed/decomposition_scenarios.csv")
    write(summary(dec), "summary")
    write(decomposition(dec), "decomposition")
    write(reviews_themes(pd.read_csv("data/processed/themes_by_segment.csv"), cov), "reviews_themes")
    write(reviews_monthly(pd.read_csv("data/processed/themes_monthly.csv"), cov), "reviews_monthly")
    matrix, evidence = competitors(pd.read_csv("data/processed/competitor_matrix.csv", dtype=str, keep_default_na=False))
    write(matrix, "competitors_matrix")
    write(evidence, "competitors_evidence")
    chart, table = pricing(pd.read_csv("data/processed/value_ladder.csv", keep_default_na=False))
    write(chart, "pricing_chart")
    write(table, "pricing")
    write(offers(pd.read_csv("data/processed/offers.csv")), "offers")
    head, grid = experiments(pd.read_csv("data/processed/experiment_sizing.csv"))
    write(head, "experiments_headline")
    write(grid, "experiments_grid")


if __name__ == "__main__":
    main()
    from src.deck.dashboard_workbook import build

    print(build())
