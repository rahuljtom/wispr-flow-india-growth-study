"""Gold-set evaluation (rule 1): tune on dev, freeze, evaluate test once.

Reads gold labels read-only; never writes to data/private/gold_*. Themes with fewer than
MIN_SUPPORT gold examples in the split are reported as "not evaluated".
"""
import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.tagging.tagger import SENTIMENTS, TAXONOMY

MIN_SUPPORT = 5


def parse_gold(df):
    g = pd.DataFrame(index=df["gold_id"].astype(str))
    # separators ";" (label guide) and "," (spreadsheet export) are both accepted
    g["themes"] = [[t.strip().lower() for t in re.split(r"[;,]", str(v)) if t.strip() and str(v) != "nan"]
                   for v in df["themes"]]
    g["sentiment"] = df["sentiment"].astype(str).str.strip().str.lower().to_numpy()
    # name (label guide) or, in the revised label file, TRUE/FALSE presence only
    g["mentions_competitor"] = pd.Series(
        [None if (pd.isna(v) or not str(v).strip() or str(v).strip().upper() == "FALSE")
         else str(v).strip() for v in df["mentions_competitor"]], index=g.index, dtype=object)
    g["is_actionable"] = [str(v).strip().lower() in ("true", "1", "yes") for v in df["is_actionable"]]
    return g


def cohens_kappa(gold, pred):
    gold, pred = list(gold), list(pred)
    n = len(gold)
    po = sum(a == b for a, b in zip(gold, pred, strict=True)) / n
    pe = sum((gold.count(c) / n) * (pred.count(c) / n) for c in set(gold) | set(pred))
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def sentiment_confusion(gold, pred, labels=("neg", "neu", "pos")):
    cm = {g: dict.fromkeys(labels, 0) for g in labels}
    for g, p in zip(gold, pred, strict=True):
        if g in cm and p in cm[g]:
            cm[g][p] += 1
    return cm


def theme_metrics(gold, pred, taxonomy):
    out = {}
    for t in taxonomy:
        tp = sum(t in g and t in p for g, p in zip(gold, pred, strict=True))
        fp = sum(t not in g and t in p for g, p in zip(gold, pred, strict=True))
        fn = sum(t in g and t not in p for g, p in zip(gold, pred, strict=True))
        out[t] = {"tp": tp, "fp": fp, "fn": fn,
                  "precision": tp / (tp + fp) if tp + fp else None,
                  "recall": tp / (tp + fn) if tp + fn else None, "support": tp + fn}
    return out


def _micro_f1(gold, pred):
    m = theme_metrics(gold, pred, TAXONOMY)
    tp = sum(v["tp"] for v in m.values())
    fp = sum(v["fp"] for v in m.values())
    fn = sum(v["fn"] for v in m.values())
    return 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0


def evaluate_split(gold, key, tags, split, seed=7, n_boot=1000):
    rows = key[key["split"] == split]
    # gold rows the labeller left unlabelled (no themes and no sentiment, e.g. non-English text) are
    # not ground truth: excluded from metrics and counted
    labelled = [bool(gold.loc[i, "themes"]) or gold.loc[i, "sentiment"] in SENTIMENTS
                for i in rows["gold_id"]]
    n_unlabelled = len(rows) - sum(labelled)
    rows = rows[labelled]
    have = rows[rows["review_key"].isin(tags)]
    gi = list(have["gold_id"])
    g_themes = [gold.loc[i, "themes"] for i in gi]
    p_themes = [tags[k]["themes"] for k in have["review_key"]]
    g_sent = [gold.loc[i, "sentiment"] for i in gi]
    p_sent = [tags[k]["sentiment"] for k in have["review_key"]]
    result = {"split": split, "n": len(have), "n_in_split": len(rows),
              "n_missing_predictions": len(rows) - len(have),
              "n_unlabelled_gold": n_unlabelled}
    if not len(have):
        return result
    result["micro_f1"] = _micro_f1(g_themes, p_themes)
    result["sentiment_kappa"] = cohens_kappa(g_sent, p_sent)
    rng = np.random.default_rng(seed)
    f1s, kps = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, len(have), len(have))
        f1s.append(_micro_f1([g_themes[i] for i in idx], [p_themes[i] for i in idx]))
        kps.append(cohens_kappa([g_sent[i] for i in idx], [p_sent[i] for i in idx]))
    result["micro_f1_ci95"] = [float(np.percentile(f1s, 2.5)), float(np.percentile(f1s, 97.5))]
    result["sentiment_kappa_ci95"] = [float(np.nanpercentile(kps, 2.5)), float(np.nanpercentile(kps, 97.5))]
    metrics = theme_metrics(g_themes, p_themes, TAXONOMY)
    result["sentiment_confusion"] = sentiment_confusion(g_sent, p_sent)
    n = len(have)
    result["all_themes_dev_diagnostic"] = {}
    for t, m in metrics.items():
        d = 2 * m["tp"] + m["fp"] + m["fn"]
        result["all_themes_dev_diagnostic"][t] = {
            **m, "tn": n - m["tp"] - m["fp"] - m["fn"], "f1": 2 * m["tp"] / d if d else None}
    result["themes"] = {}
    for t, m in metrics.items():
        if m["support"] < MIN_SUPPORT:
            result["themes"][t] = {"status": "not evaluated", "support": m["support"]}
        else:
            result["themes"][t] = {"status": "evaluated", **m}
    f1 = {t: (2 * v["tp"] / (2 * v["tp"] + v["fp"] + v["fn"])) for t, v in result["themes"].items()
          if v["status"] == "evaluated"}
    worst = sorted(f1, key=f1.get)[:3]
    result["worst_themes"] = {t: {"f1": f1[t], "disagreeing_gold_ids": [
        i for i, g, p in zip(gi, g_themes, p_themes, strict=True) if (t in g) != (t in p)][:5]}
        for t in worst}
    return result


def freeze(config, interim_dir="data/interim"):
    path = Path(interim_dir) / "frozen_config.json"
    if path.exists():
        raise PermissionError("config already frozen; a new freeze requires an explicit decision")
    path.write_text(json.dumps({**config, "frozen_utc": datetime.now(UTC).isoformat(
        timespec="seconds")}, indent=1))
    return path


def refreeze(config, reason, interim_dir="data/interim"):
    """Replace the frozen config on an explicit decision; the old one is archived."""
    if not reason.strip():
        raise ValueError("re-freeze needs a recorded reason")
    interim = Path(interim_dir)
    path = interim / "frozen_config.json"
    old = json.loads(path.read_text())
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    (interim / f"frozen_config_superseded_{stamp}.json").write_text(json.dumps(old, indent=1))
    path.unlink()
    out = freeze({**config, "supersedes": old.get("prompt_version"), "reason": reason}, interim_dir)
    return out


def assert_model_prompt_frozen(model_id, prompt_version, interim_dir="data/interim"):
    path = Path(interim_dir) / "frozen_config.json"
    if not path.exists():
        raise PermissionError("bulk tagging needs a frozen config")
    cfg = json.loads(path.read_text())
    if cfg.get("model_id") != model_id or cfg.get("prompt_version") != prompt_version:
        raise PermissionError("model/prompt differ from the frozen config")


def assert_frozen_matches(model_id, prompt_version, interim_dir="data/interim"):
    path = Path(interim_dir) / "frozen_config.json"
    if not path.exists():
        raise PermissionError("test split needs a frozen config (run freeze first)")
    cfg = json.loads(path.read_text())
    if cfg.get("model_id") != model_id or cfg.get("prompt_version") != prompt_version:
        raise PermissionError("model/prompt differ from the frozen config")
    if (Path(interim_dir) / "eval_test.json").exists():
        raise PermissionError("test split already evaluated once")


def run_cli_split(split, tags_path, private_dir="data/private", interim_dir="data/interim",
                  n_boot=1000):
    interim = Path(interim_dir)
    if split == "test":
        if not (interim / "frozen_config.json").exists():
            raise PermissionError("test split needs a frozen config (run freeze first)")
        if (interim / "eval_test.json").exists():
            raise PermissionError("test split is evaluated once; eval_test.json exists")
    gold = parse_gold(pd.read_csv(Path(private_dir) / "gold_labels.csv"))
    key = pd.read_csv(Path(private_dir) / "gold_split_key.csv")
    res = evaluate_split(gold, key, json.loads(Path(tags_path).read_text()), split, n_boot=n_boot)
    if split == "dev":
        out = interim / f"eval_dev_{Path(tags_path).stem}.json"
    else:
        out = interim / "eval_test.json"
    out.write_text(json.dumps(res, indent=1))
    return res


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("eval")
    e.add_argument("split", choices=["dev", "test"])
    e.add_argument("tags")
    f = sub.add_parser("freeze")
    f.add_argument("--model", required=True)
    f.add_argument("--prompt-version", required=True)
    f.add_argument("--rpm", type=float)
    f.add_argument("--reason", help="re-freeze over an existing config (explicit decision)")
    a = ap.parse_args()
    if a.cmd == "freeze":
        cfg = {"model_id": a.model, "prompt_version": a.prompt_version, "rpm": a.rpm}
        print(refreeze(cfg, a.reason) if a.reason else freeze(cfg))
    else:
        r = run_cli_split(a.split, a.tags)
        print(json.dumps({k: v for k, v in r.items() if k != "themes"}, indent=1))


if __name__ == "__main__":
    main()
