"""Gold-set sampling and blind label files (rules 1, 2).

Strata: store x country x rating x detected language. Every non-empty stratum gets at least one
review (if the stratum count fits the sample size); the rest is allocated proportionally to
stratum size, capped at availability. Small strata are therefore slightly over-represented
relative to their population share; actual counts are recorded, never padded.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

STRATA = ["store", "country", "rating", "lang_detected"]
LABEL_COLS = ["themes", "sentiment", "mentions_competitor", "is_actionable"]


def stratified_sample(df, n, seed=7, strata=STRATA):
    df = df[df["text_clean"].fillna("").str.len() >= 3].drop_duplicates("review_key")
    rng = np.random.default_rng(seed)
    groups = {k: g for k, g in df.groupby(strata)}
    avail = {k: len(g) for k, g in groups.items()}
    alloc = dict.fromkeys(groups, 0)
    if len(groups) <= n:
        alloc = dict.fromkeys(groups, 1)
    remaining = n - sum(alloc.values())
    total = sum(avail.values())
    while remaining > 0:
        room = {k: avail[k] - alloc[k] for k in groups if avail[k] > alloc[k]}
        if not room:
            break
        weight = {k: avail[k] / total for k in room}
        quota = {k: weight[k] * remaining for k in room}
        add = {k: min(int(quota[k]), room[k]) for k in room}
        left = remaining - sum(add.values())
        for k in sorted(room, key=lambda k: quota[k] - int(quota[k]), reverse=True):
            if left <= 0:
                break
            if add[k] < room[k]:
                add[k] += 1
                left -= 1
        for k, v in add.items():
            alloc[k] += v
        remaining = n - sum(alloc.values())
    parts = []
    for k in sorted(groups):
        g = groups[k]
        idx = rng.permutation(len(g))[: alloc[k]]
        parts.append(g.iloc[idx])
    sample = pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)
    counts = {
        "seed": seed, "requested": n, "n_sampled": len(sample),
        "n_strata_available": len(groups),
        "n_strata_sampled": sum(1 for v in alloc.values() if v > 0),
        "strata": [dict(zip(strata, (v.item() if hasattr(v, "item") else v for v in k), strict=True))
                   | {"available": avail[k], "sampled": alloc[k]} for k in sorted(groups)],
    }
    return sample, counts


def split_dev_test(sample, seed=7, n_dev=40):
    rng = np.random.default_rng(seed)
    out = sample.copy()
    out["split"] = "test"
    out.loc[out.index[rng.permutation(len(out))[:n_dev]], "split"] = "dev"
    return out


def make_gold_files(df, out_dir, seed=7, n=100):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sample, counts = stratified_sample(df, n, seed)
    sample = split_dev_test(sample, seed)
    sample["gold_id"] = [f"gold_{i + 1:03d}" for i in range(len(sample))]
    blind = sample[["gold_id", "text_clean"]].rename(columns={"text_clean": "text"})
    for c in LABEL_COLS:
        blind[c] = ""
    blind.to_csv(out_dir / "gold_blind.csv", index=False)
    sample[["gold_id", "review_key", "split", *STRATA]].to_csv(out_dir / "gold_split_key.csv",
                                                             index=False)
    (out_dir / "gold_strata_counts.json").write_text(json.dumps(counts, indent=1))
    return out_dir / "gold_blind.csv", out_dir / "gold_split_key.csv", counts


def main(argv=None):
    """CLI: write the blind gold-set files; refuses to overwrite existing ones (labels may depend on them)."""
    import argparse

    ap = argparse.ArgumentParser(description=main.__doc__)
    ap.add_argument("--input", default="data/processed/wispr_reviews.csv")
    ap.add_argument("--out", default="data/private")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args(argv)
    out = Path(a.out)
    for name in ("gold_blind.csv", "gold_split_key.csv"):
        if (out / name).exists():
            raise FileExistsError(f"{out / name} exists; move it away deliberately before regenerating")
    make_gold_files(pd.read_csv(a.input), out, seed=a.seed)


if __name__ == "__main__":
    main()
