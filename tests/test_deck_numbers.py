"""Cross-check headline ledger values against recomputation from source data."""
import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from src.analysis.decomposition import decompose, scenario_grid

LEDGER = Path("data/ledger/numbers_ledger.csv")


def load(path):
    return json.loads(Path(path).read_text())


def val(cid):
    for r in csv.DictReader(LEDGER.open()):
        if r["claim_id"] == cid:
            return r["value"]
    pytest.skip(f"{cid} not in ledger")


def test_decomposition_ledger_matches_recomputation():
    d = decompose(0.14, 0.02, 3.4, 12.0)
    assert float(val("R-011")) == pytest.approx(round(d["rev_per_install_index"], 3))
    assert float(val("R-012")) == pytest.approx(round(d["price_index"], 3))
    assert float(val("R-013")) == pytest.approx(round(d["residual_index"], 3))
    g = scenario_grid(0.14, 0.02, 3.4, 12.0, 212, 61)
    assert val("R-014") == f"{g.residual_index.min():.2f}-{g.residual_index.max():.2f}"


def test_price_and_fx_arithmetic():
    assert float(val("R-072")) == 320 * 12
    assert float(val("R-016")) == pytest.approx(round(320 / 3.4, 1))
    assert float(val("R-100")) == pytest.approx(2_500_000 * 0.14 / 212, abs=50)


def test_tagging_metrics_match_eval_files():
    t = load("data/interim/eval_test.json")
    assert float(val("R-040")) == pytest.approx(round(t["micro_f1"], 3))
    assert float(val("R-041")) == pytest.approx(round(t["sentiment_kappa"], 3))
    d = load("data/interim/eval_dev_dev_v3.json")
    assert float(val("R-103")) == pytest.approx(round(d["micro_f1"], 3))
    assert t["split"] == "test" and t["n"] == 60 and d["n"] == 40


def test_theme_claims_match_themes_table():
    th = pd.read_csv("data/processed/themes_by_segment.csv")
    a = th[th.segment == "all tagged sample"]
    cov = load("data/processed/a1_coverage.json")
    assert int(val("R-050")) == int(a.n_segment.iloc[0]) == cov["tagged"]
    top = a[a.theme != "other"].sort_values("share", ascending=False).head(3)
    for k, (_, r) in enumerate(top.iterrows()):
        assert float(val(f"R-05{k + 1}")) == pytest.approx(round(r.share * 100, 1))
    assert (th[th.suppressed].share.isna()).all()  # suppressed cells stay blank


def test_sizing_headline_cells_match_table():
    s = pd.read_csv("data/processed/experiment_sizing.csv")
    for k, (name, g) in enumerate(s.groupby("experiment")):
        base, mde = {"E1": (0.3, 0.05), "E2": (0.02, 0.01), "E3": (0.2, 0.04)}[name[:2]]
        c = g[(g.baseline == base) & (g.mde_abs == mde)]
        v = val(f"R-06{k}")
        assert f"{int(c.n_per_arm.iloc[0])}" in v and f"{c.total_days.min()}-{c.total_days.max()}" in v


@pytest.mark.skipif(not (Path("data/private/gold_split_key.csv").exists() and Path("data/private/gold_labels.csv").exists()),
                    reason="gold labels are private and not distributed with the repository")
def test_gold_files_untouched_structure():
    key = pd.read_csv("data/private/gold_split_key.csv")
    lab = pd.read_csv("data/private/gold_labels.csv", dtype=str, keep_default_na=False)
    assert list(key.gold_id) == list(lab.gold_id) and key.split.value_counts().to_dict() == {"test": 60, "dev": 40}
