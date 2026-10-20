"""P6 modules that do not depend on review tagging: A3 trends, A4 decomposition, A7 sizing."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.analysis.decomposition import run_grid
from src.analysis.sizing import sizing_table
from src.analysis.trends import did_estimate, index_series, pre_stats, usable
from src.common.ledger import add_claim, read_ledger

EVENT = pd.Timestamp("2026-04-27")  # provisional campaign-live date (DECISIONS #3)
CHARTS = Path("outputs/charts")
PROC = Path("data/processed")


def ledger_once(claim_id, *args, **kw):
    if not any(r["claim_id"] == claim_id for r in read_ledger()):
        add_claim(claim_id, *args, **kw)


def a4():
    g = run_grid(0.14, 0.02, 3.4, 12.0, window_days=212, price_start_day=61)
    point = g[(g.missed_share == 0) & (g.price_window_share == 1.0)].iloc[0]
    d = {"rev_per_install_index": point.rev_per_install_index, "price_index": point.price_index,
         "residual_index": point.residual_index}
    g.to_csv(PROC / "decomposition_scenarios.csv", index=False)
    lo, hi = g.residual_index.min(), g.residual_index.max()
    rlo, rhi = g.rev_per_install_index.min(), g.rev_per_install_index.max()
    ledger_once("R-011", "slide 3", "India revenue-per-install index vs global", round(d["rev_per_install_index"], 3),
                "ratio", "derived", derivation="R-003 / R-002 (2% / 14%)")
    ledger_once("R-012", "slide 3", "India price index (India price / global price)", round(d["price_index"], 3),
                "ratio", "derived", derivation="R-010 / R-005 (3.4 / 12), FX as stated by TechCrunch")
    ledger_once("R-013", "slide 3", "Residual index (revenue-per-install / price index)", round(d["residual_index"], 3),
                "ratio", "derived", derivation="R-011 / R-012; scenario decomposition, not causal")
    ledger_once("R-014", "slide 3", "Residual index range under sensitivity grid", f"{lo:.2f}-{hi:.2f}", "ratio",
                "derived", derivation="grid: missed India revenue 0-60% x price applying to 50%-100% of window; "
                "inputs R-002, R-003, R-005, R-010", caveat="Scenario range; assumptions in ASSUMPTIONS.md")
    ledger_once("R-015", "slide 3", "Revenue-per-install index range under sensitivity grid",
                f"{rlo:.2f}-{rhi:.2f}", "ratio", "derived", derivation="grid over missed India revenue 0-60%; "
                "inputs R-002, R-003")
    return d, (lo, hi), (rlo, rhi)


def a3():
    out = {}
    series = {}
    for q in ["wispr_flow", "whisper_flow", "wisper_flow", "whispr_flow"]:
        df = pd.read_csv(f"data/interim/trends_{q}.csv", parse_dates=["date"])
        st = {g: pre_stats(df, g, EVENT) for g in df.geo.unique()}
        ok = {g: usable(s) for g, s in st.items()}
        res = did_estimate(df, "IN-KA", ["IN-MH", "IN-DL", "IN-TN", "IN-TG"], EVENT)
        out[q] = {"usable_geos": [g for g, v in ok.items() if v], "pre_stats": st,
                  "did": {k: v for k, v in res.items() if k != "pre_stats"}}
        if q == "wispr_flow":
            series = {g: index_series(df, g, EVENT) for g, v in ok.items() if v}
    Path("data/processed/trends_summary.json").write_text(json.dumps(out, indent=1, default=str))
    if series:
        pd.DataFrame(series).rename_axis("date").to_csv(PROC / "trends_event_study.csv")
        fig, ax = plt.subplots(figsize=(7, 3.8))
        for g, s in series.items():
            ax.plot(s.index, s.values, label=g, lw=2 if g == "IN-KA" else 1.2)
        ax.axvline(EVENT, color="grey", ls="--")
        ax.set_ylabel("Search interest index\n(own pre-period mean = 100)", fontsize=8)
        ax.set_title('"wispr flow" Google Trends, weekly (directional; provisional campaign date)', fontsize=9)
        ax.legend(fontsize=8)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(CHARTS / "trends_event_study.png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        (CHARTS / "trends_event_study.json").write_text(json.dumps({"labels": []}))
    return out


def a7():
    t = sizing_table()
    t.to_csv(PROC / "experiment_sizing.csv", index=False)
    return t


if __name__ == "__main__":
    CHARTS.mkdir(parents=True, exist_ok=True)
    print(a4())
    t3 = a3()
    print(json.dumps({q: {"usable": v["usable_geos"], "status": v["did"]["status"],
                          "reason": v["did"].get("reason")} for q, v in t3.items()}, indent=1))
    print(len(a7()), "sizing rows")
