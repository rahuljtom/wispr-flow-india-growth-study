"""Seeded sample for bulk tagging: non-gold reviews, proportional allocation over store x rating."""
import json
from pathlib import Path

import numpy as np
import pandas as pd


def select_sample(df, gold_keys, n, seed):
    pool = df[~df["review_key"].isin(gold_keys) & (df["text_clean"].fillna("").str.len() >= 3)]
    pool = pool.drop_duplicates("review_key")
    groups = {k: g for k, g in pool.groupby(["store", "rating"])}
    total = len(pool)
    quota = {k: len(g) * n / total for k, g in groups.items()}
    alloc = {k: min(int(q), len(groups[k])) for k, q in quota.items()}
    left = n - sum(alloc.values())
    for k in sorted(quota, key=lambda k: quota[k] - int(quota[k]), reverse=True):
        if left <= 0:
            break
        if alloc[k] < len(groups[k]):
            alloc[k] += 1
            left -= 1
    rng = np.random.default_rng(seed)
    parts = [groups[k].iloc[rng.permutation(len(groups[k]))[: alloc[k]]] for k in sorted(groups)]
    sample = pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)
    counts = {
        "seed": seed, "requested": n, "n_sampled": len(sample), "pool_size_non_gold": total,
        "n_gold_excluded": int(df["review_key"].isin(gold_keys).sum()),
        "by_store": {k: int(v) for k, v in sample.groupby("store").size().items()},
        "by_store_country": {f"{a}/{b}": int(v) for (a, b), v in sample.groupby(["store", "country"]).size().items()},
        "by_rating": {str(k): int(v) for k, v in sample.groupby("rating").size().items()},
        "by_language": {k: int(v) for k, v in sample.groupby("lang_detected").size().items()},
        "pool_by_language": {k: int(v) for k, v in pool.groupby("lang_detected").size().items()},
        "strata": [{"store": a, "rating": int(b), "available": len(groups[(a, b)]),
                    "sampled": alloc[(a, b)]} for (a, b) in sorted(groups)],
    }
    return sample, counts


def main(n=600, seed=20261018):
    df = pd.read_csv("data/processed/wispr_reviews.csv")
    gold = set(pd.read_csv("data/private/gold_split_key.csv")["review_key"])
    sample, counts = select_sample(df, gold, n, seed)
    Path("data/interim").mkdir(exist_ok=True)
    sample[["review_key"]].to_csv("data/interim/bulk_sample_ids.csv", index=False)
    Path("data/interim/bulk_sample_counts.json").write_text(json.dumps(counts, indent=1))
    return counts


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in main().items() if k != "strata"}, indent=1))
