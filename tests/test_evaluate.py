import json

import pandas as pd
import pytest

from src.tagging.evaluate import (
    cohens_kappa,
    evaluate_split,
    freeze,
    parse_gold,
    run_cli_split,
    theme_metrics,
)


def test_kappa_known_values():
    a = ["pos", "pos", "neg", "neu"]
    assert cohens_kappa(a, a) == 1.0
    # classic 2x2 example: po=0.7, pe=0.5 -> 0.4
    g = ["pos"] * 5 + ["neg"] * 5
    p = ["pos"] * 4 + ["neg"] + ["pos"] * 2 + ["neg"] * 3
    assert cohens_kappa(g, p) == pytest.approx(0.4)


def test_theme_metrics_precision_recall_support():
    gold = [["a", "b"], ["a"], ["b"], ["c"]]
    pred = [["a"], ["a", "b"], ["b"], ["a"]]
    m = theme_metrics(gold, pred, ["a", "b", "c"])
    assert m["a"] == {"tp": 2, "fp": 1, "fn": 0, "precision": 2 / 3, "recall": 1.0, "support": 2}
    assert m["b"]["precision"] == 0.5 and m["b"]["recall"] == 0.5 and m["b"]["support"] == 2
    assert m["c"]["recall"] == 0.0 and m["c"]["precision"] is None  # no predictions of c


def labels_df(n=12):
    return pd.DataFrame({
        "gold_id": [f"gold_{i:03d}" for i in range(n)],
        "themes": ["ui_ux;latency_speed"] * n, "sentiment": ["pos"] * n,
        "mentions_competitor": [""] * n, "is_actionable": ["true"] * n})


def test_parse_gold_handles_blank_and_case():
    df = labels_df(2)
    df.loc[0, "themes"] = " UI_UX ; latency_speed "
    df.loc[1, "mentions_competitor"] = "Gboard"
    g = parse_gold(df)
    assert g.loc["gold_000", "themes"] == ["ui_ux", "latency_speed"]
    assert g.loc["gold_001", "mentions_competitor"] == "Gboard"
    assert g.loc["gold_000", "mentions_competitor"] is None
    assert bool(g.loc["gold_000", "is_actionable"])


def test_evaluate_split_marks_low_support_not_evaluated_and_has_ci():
    n = 12
    gold = parse_gold(labels_df(n))
    key = pd.DataFrame({"gold_id": gold.index, "review_key": [f"k{i}" for i in range(n)],
                        "split": ["test"] * n})
    tags = {f"k{i}": {"themes": ["ui_ux"], "sentiment": "pos", "mentions_competitor": None,
                      "is_actionable": True} for i in range(n)}
    r = evaluate_split(gold, key, tags, "test", seed=1, n_boot=200)
    assert r["n"] == 12 and r["n_missing_predictions"] == 0
    assert r["themes"]["ui_ux"]["status"] == "evaluated"
    assert r["themes"]["accuracy_general"]["status"] == "not evaluated"  # support < 5
    lo, hi = r["micro_f1_ci95"]
    assert lo <= r["micro_f1"] <= hi


def test_missing_predictions_reported_not_hidden():
    gold = parse_gold(labels_df(6))
    key = pd.DataFrame({"gold_id": gold.index, "review_key": [f"k{i}" for i in range(6)],
                        "split": ["dev"] * 6})
    r = evaluate_split(gold, key, {"k0": {"themes": ["ui_ux"], "sentiment": "pos",
                                           "mentions_competitor": None, "is_actionable": True}},
                       "dev", n_boot=50)
    assert r["n_missing_predictions"] == 5


def test_test_split_requires_freeze_and_runs_once(tmp_path):
    d = tmp_path
    labels_df(6).to_csv(d / "gold_labels.csv", index=False)
    before = (d / "gold_labels.csv").read_bytes()
    pd.DataFrame({"gold_id": labels_df(6).gold_id, "review_key": [f"k{i}" for i in range(6)],
                  "split": ["test"] * 6}).to_csv(d / "gold_split_key.csv", index=False)
    tags = d / "tags.json"
    tags.write_text(json.dumps({f"k{i}": {"themes": ["ui_ux"], "sentiment": "pos",
                                          "mentions_competitor": None, "is_actionable": True}
                                for i in range(6)}))
    with pytest.raises(PermissionError, match="freeze"):
        run_cli_split("test", tags, private_dir=d, interim_dir=d)
    freeze({"model_id": "m", "prompt_version": "v1"}, interim_dir=d)
    run_cli_split("test", tags, private_dir=d, interim_dir=d, n_boot=20)
    assert (d / "eval_test.json").exists()
    with pytest.raises(PermissionError, match="once"):
        run_cli_split("test", tags, private_dir=d, interim_dir=d, n_boot=20)
    # gold labels untouched
    assert (d / "gold_labels.csv").read_bytes() == before


def test_unlabelled_gold_rows_excluded_and_counted():
    df = labels_df(6)
    df.loc[0, ["themes", "sentiment"]] = ["", ""]  # labeller skipped (e.g. non-English)
    gold = parse_gold(df)
    key = pd.DataFrame({"gold_id": gold.index, "review_key": [f"k{i}" for i in range(6)],
                        "split": ["dev"] * 6})
    tag = {"themes": ["ui_ux"], "sentiment": "pos", "mentions_competitor": None, "is_actionable": True}
    r = evaluate_split(gold, key, {f"k{i}": tag for i in range(6)}, "dev", n_boot=20)
    assert r["n"] == 5 and r["n_unlabelled_gold"] == 1


def test_confusion_matrices_and_all_theme_table():
    from src.tagging.evaluate import sentiment_confusion

    cm = sentiment_confusion(["pos", "pos", "neg"], ["pos", "neg", "neg"])
    assert cm["pos"]["pos"] == 1 and cm["pos"]["neg"] == 1 and cm["neg"]["neg"] == 1
    gold = parse_gold(labels_df(6))
    key = pd.DataFrame({"gold_id": gold.index, "review_key": [f"k{i}" for i in range(6)],
                        "split": ["dev"] * 6})
    tag = {"themes": ["ui_ux"], "sentiment": "pos", "mentions_competitor": None, "is_actionable": True}
    r = evaluate_split(gold, key, {f"k{i}": tag for i in range(6)}, "dev", n_boot=20)
    assert r["sentiment_confusion"]["pos"]["pos"] == 6
    t = r["all_themes_dev_diagnostic"]["ui_ux"]
    assert {"tp", "fp", "fn", "tn", "precision", "recall", "f1", "support"} <= set(t)


def test_parse_gold_accepts_spreadsheet_format():
    df = labels_df(3)
    df.loc[0, "themes"] = "praise_productivity, accuracy_general"
    df.loc[1, "mentions_competitor"] = "TRUE"
    df.loc[2, "mentions_competitor"] = "FALSE"
    df["is_actionable"] = ["TRUE", "FALSE", "TRUE"]
    g = parse_gold(df)
    assert g.loc["gold_000", "themes"] == ["praise_productivity", "accuracy_general"]
    assert g.loc["gold_001", "mentions_competitor"] == "TRUE" and g.loc["gold_002", "mentions_competitor"] is None
    assert [bool(x) for x in g.is_actionable] == [True, False, True]


def test_refreeze_archives_previous_and_needs_reason(tmp_path):
    from src.tagging.evaluate import refreeze

    freeze({"model_id": "m", "prompt_version": "v2"}, interim_dir=tmp_path)
    with pytest.raises(ValueError):
        refreeze({"model_id": "m", "prompt_version": "v3"}, "", interim_dir=tmp_path)
    refreeze({"model_id": "m", "prompt_version": "v3"}, "labels revised", interim_dir=tmp_path)
    cur = json.loads((tmp_path / "frozen_config.json").read_text())
    assert cur["prompt_version"] == "v3" and cur["supersedes"] == "v2" and "labels revised" in cur["reason"]
    old = list(tmp_path.glob("frozen_config_superseded_*.json"))
    assert len(old) == 1 and json.loads(old[0].read_text())["prompt_version"] == "v2"


def test_bulk_guard_requires_matching_frozen_config(tmp_path):
    from src.tagging.evaluate import assert_model_prompt_frozen

    with pytest.raises(PermissionError):
        assert_model_prompt_frozen("m", "v3", interim_dir=tmp_path)
    freeze({"model_id": "m", "prompt_version": "v3"}, interim_dir=tmp_path)
    assert_model_prompt_frozen("m", "v3", interim_dir=tmp_path)
    with pytest.raises(PermissionError):
        assert_model_prompt_frozen("m", "v2", interim_dir=tmp_path)
