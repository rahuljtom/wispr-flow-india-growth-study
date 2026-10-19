"""A4: scenario decomposition of the India install-vs-revenue gap (rule 6).

An arithmetic identity, not a causal attribution: revenue-per-install index = price index x
residual index. The residual lumps conversion, mix, measurement and anything else.
"""
import itertools

import pandas as pd


def decompose(install_share, rev_share, india_price, global_price):
    rpi = rev_share / install_share
    price = india_price / global_price
    return {"rev_per_install_index": rpi, "price_index": price, "residual_index": rpi / price}


def adjusted_share(rev_share, missed_share):
    """India revenue share if a fraction of India revenue is missing from the source
    (global revenue assumed fully observed; an upper-bound scenario)."""
    india = rev_share / (1 - missed_share)
    return india / (india + (1 - rev_share))


def scenario_grid(install_share, rev_share, india_price, global_price, window_days, price_start_day,
                  missed=(0.0, 0.2, 0.4, 0.6)):
    full = (window_days - price_start_day) / window_days
    rows = []
    for m, f in itertools.product(missed, sorted({0.5, full, 1.0})):
        rpi = adjusted_share(rev_share, m) / install_share
        price = (1 - f) + f * india_price / global_price
        rows.append({"missed_share": m, "price_window_share": f, "rev_per_install_index": rpi,
                     "price_index": price, "residual_index": rpi / price})
    return pd.DataFrame(rows)
