"""Charts for the deck (bars start at zero; units on axes; one palette)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BLUE, ORANGE, GREY = "#3b6ea8", "#e07b39", "#8a8a8a"
OUT = Path("outputs/charts")


def _clean(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def gap_decomposition():
    g = pd.read_csv("data/processed/decomposition_scenarios.csv")
    lo, hi = g.residual_index.min(), g.residual_index.max()
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1, 1.5]})
    a.bar(["Installs", "In-app\nrevenue"], [14, 2], color=[BLUE, ORANGE], width=0.55)
    a.set_ylim(0, 17)
    a.set_ylabel("India share of total (%)")
    for i, v in enumerate([14, 2]):
        a.text(i, v + 0.4, f"{v}%", ha="center", fontsize=11, fontweight="bold")
    a.set_title("Reported (Oct 2025 to Apr 2026,\nin-app purchases only)", fontsize=10)
    vals = [("Revenue per\ninstall", 0.143, BLUE), ("Price index\n(3.4 / 12 USD)", 0.283, ORANGE),
            ("Residual\n(everything else)", 0.504, GREY)]
    b.bar([v[0] for v in vals], [v[1] for v in vals], color=[v[2] for v in vals], width=0.55)
    b.set_ylim(0, 1.4)
    b.set_ylabel("Index vs global rate (ratio)")
    for i, v in enumerate(vals):
        b.text(i - 0.28, v[1] + 0.03, f"{v[1]:.3f}", ha="left", fontsize=10, fontweight="bold")
    b.vlines(2.38, lo, hi, color="black", lw=2)
    b.text(2.43, hi, f"{hi:.2f}", va="center", fontsize=9)
    b.text(2.43, lo, f"{lo:.2f}", va="center", fontsize=9)
    b.set_xlim(-0.5, 2.9)
    b.set_title("Scenario decomposition (identity, not causal);\nblack bar = residual range across scenarios", fontsize=10)
    for ax in (a, b):
        _clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "gap_decomposition.png", dpi=200)
    plt.close(fig)
    (OUT / "gap_decomposition.json").write_text(
        json.dumps({"labels": ["14%", "2%", "0.143", "0.283", "0.504", f"{lo:.2f}", f"{hi:.2f}"]}))


def price_ladder():
    d = pd.read_csv("data/processed/value_ladder.csv")
    d = d[d.price_inr_per_month.notna()].copy()
    d["label"] = (d["product"] + " " + d["plan"].replace({"India Pro": "India"}) + " (billed "
                  + d["billing"].map({"annual": "annually", "monthly": "monthly"}) + ")")
    d = d.sort_values("price_inr_per_month")
    colors = [ORANGE if "Wispr" in p else GREY for p in d["product"]]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.barh(d.label, d.price_inr_per_month, color=colors)
    ax.set_xlim(0, d.price_inr_per_month.max() * 1.15)
    ax.set_xlabel("INR per user per month (USD list prices at 94.1 INR per USD)")
    for y, v in enumerate(d.price_inr_per_month):
        ax.text(v + 15, y, f"{int(v)}", va="center", fontsize=9)
    ax.set_title("Paid-tier price per month (orange = Wispr Flow)", fontsize=10)
    _clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "price_ladder.png", dpi=200)
    plt.close(fig)
    (OUT / "price_ladder.json").write_text(json.dumps({"labels": [str(int(v)) for v in d.price_inr_per_month]}))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    gap_decomposition()
    price_ladder()
