"""A5: effective INR per month per product/tier at the FX implied by TechCrunch (R-004 / R-010)."""
import pandas as pd

from src.common.ledger import add_claim, read_ledger
from src.common.sql import run_sql

FX = 320 / 3.4  # INR per USD, implied by TechCrunch's own conversion (May 2026); no independent FX source


def build():
    df = pd.read_csv("data/processed/competitor_pricing.csv")
    df = run_sql("value_ladder.sql", {"fx": FX, "india_annual_inr": 320.0, "india_monthly_inr": 400.0},
                 {"pricing": df})  # India page R-071 (annual) and R-070 (monthly)
    df.to_csv("data/processed/value_ladder.csv", index=False)
    return df


def ledger(df):
    have = {r["claim_id"] for r in read_ledger()}
    if "R-016" not in have:
        add_claim("R-016", "slide 7", "Implied FX rate INR per USD", round(FX, 1), "INR/USD", "derived",
                  derivation="R-004 / R-010 (320 / 3.4)", caveat="Rounded USD figure in source; not independent")
    n = 17
    for _, r in df.iterrows():
        cid = f"R-{n:03d}"
        n += 1
        if cid in have or pd.isna(r["price_inr_per_month"]) or r["plan"] == "India Pro":
            continue
        add_claim(cid, "slide 7", f"{r['product']} {r['plan']} ({r['billing']}) in INR per month",
                  int(r["price_inr_per_month"]), "INR/month", "derived",
                  derivation=f"price_usd {r['price_usd_per_month']} x R-016",
                  caveat="USD list price converted at implied FX")


if __name__ == "__main__":
    d = build()
    ledger(d)
    print(d[["product", "plan", "billing", "price_usd_per_month", "price_inr_per_month"]])
