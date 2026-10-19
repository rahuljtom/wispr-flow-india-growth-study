import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from src.analysis.run_a1 import partial_tags_from_cache
from src.pulls.pricing_snapshots import parse_snapshots
from src.tagging.gold import main as gold_main


def test_parse_snapshots_extracts_usd_tokens_and_flags_inr(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "wispr_20251009143925.html").write_text(
        "<html><script>var x=1</script><body>Pro $12 / user / mo billed annually. $15/mo. "
        "2,000 words per week on desktop</body></html>")
    (raw / "wispr_20260101000000.html").write_text("<body>₹320 per month. $12/mo</body>")
    out = tmp_path / "snap.csv"
    parse_snapshots(raw_dir=raw, out=out)
    rows = list(csv.DictReader(out.open()))
    assert [r["snapshot_utc"] for r in rows] == ["20251009143925", "20260101000000"]
    assert "$12/user/mo" in rows[0]["usd_per_month_tokens"] and rows[0]["inr_price_present"] == "false"
    assert rows[1]["inr_price_present"] == "true"
    assert rows[1]["archive_url"].endswith("/https://wisprflow.ai/pricing")


@pytest.mark.skipif(not Path("data/raw/pricing").exists(), reason="raw archive snapshots are not distributed")
def test_parse_snapshots_reproduces_committed_table(tmp_path):
    out = tmp_path / "s.csv"
    parse_snapshots(out=out)
    assert out.read_text() == Path("data/processed/pricing_snapshots.csv").read_text()


def test_gold_cli_refuses_to_overwrite_existing_gold_files(tmp_path):
    reviews = pd.DataFrame({
        "review_key": [f"k{i}" for i in range(300)], "store": ["play"] * 300, "country": ["x"] * 300,
        "rating": [i % 5 + 1 for i in range(300)], "lang_detected": ["en"] * 300,
        "text_clean": [f"review {i}" for i in range(300)]})
    src = tmp_path / "reviews.csv"
    reviews.to_csv(src, index=False)
    out = tmp_path / "private"
    gold_main(["--input", str(src), "--out", str(out)])
    assert (out / "gold_blind.csv").exists() and (out / "gold_split_key.csv").exists()
    before = (out / "gold_split_key.csv").read_bytes()
    with pytest.raises(FileExistsError):
        gold_main(["--input", str(src), "--out", str(out)])
    assert (out / "gold_split_key.csv").read_bytes() == before


def test_partial_tags_from_cache_uses_frozen_config_and_sample_only(tmp_path):
    cache = {"k1|v3|m": {"themes": ["other"]}, "k2|v3|m": {"themes": ["ui_ux"]},
             "k3|v2|m": {"themes": ["other"]}, "k4|v3|other-model": {"themes": ["other"]}}
    (tmp_path / "cache.json").write_text(json.dumps(cache))
    (tmp_path / "ids.csv").write_text("review_key\nk1\nk3\nk4\nk9\n")
    (tmp_path / "frozen.json").write_text(json.dumps({"model_id": "m", "prompt_version": "v3"}))
    out = partial_tags_from_cache(cache=tmp_path / "cache.json", ids=tmp_path / "ids.csv",
                                  frozen=tmp_path / "frozen.json", out=tmp_path / "partial.json")
    assert json.loads(out.read_text()) == {"k1": {"themes": ["other"]}}  # k2 not in sample, k3 wrong prompt, k4 wrong model
