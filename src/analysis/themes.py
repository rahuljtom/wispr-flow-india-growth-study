"""A1: theme shares with Wilson intervals; cells with n < MIN_N are suppressed (methodology rule: suppress small cells).

Shares are shares of reviews in the segment that carry a theme (a review can carry up to 3), so
they do not sum to 1. Results describe the tagged sample only.
"""
import math

import pandas as pd

from src.tagging.tagger import TAXONOMY

MIN_N = 30
Z = 1.959964


def wilson(k, n, z=Z):
    if n == 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def theme_table(df, segment):
    n = len(df)
    rows = []
    for t in TAXONOMY:
        has = df["themes"].map(lambda ts, t=t: t in ts)
        k = int(has.sum())
        sup = n < MIN_N
        lo, hi = (None, None) if sup else wilson(k, n)
        rows.append({"segment": segment, "theme": t, "n_segment": n, "n_with_theme": k,
                     "share": None if sup else k / n, "ci_lo": lo, "ci_hi": hi,
                     "mean_rating": None if sup or k == 0 else float(df.loc[has, "rating"].mean()),
                     "suppressed": sup})
    out = pd.DataFrame(rows)
    return out.astype({"share": "float64", "ci_lo": "float64", "ci_hi": "float64",
                       "mean_rating": "float64"})
