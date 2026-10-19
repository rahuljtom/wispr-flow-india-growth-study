import json

import pandas as pd
import pytest

from src.tagging.gold import make_gold_files, split_dev_test, stratified_sample
from src.tagging.tagger import (
    PROMPT_VERSION,
    TAXONOMY,
    Cache,
    build_payload,
    estimate_cost,
    tag_reviews,
    validate_tag,
)

GOOD = {"themes": ["latency_speed", "praise_productivity"], "sentiment": "pos",
        "mentions_competitor": None, "is_actionable": False}


def df_reviews(n=10, text="Call me at +91 98765 43210 or a@b.com @me http://x.co great app"):
    return pd.DataFrame({"review_key": [f"k{i}" for i in range(n)], "text_clean": [text] * n})


def test_validate_tag_accepts_good_rejects_bad():
    assert validate_tag(GOOD) == GOOD
    for bad in (
        {**GOOD, "themes": ["nonsense"]},
        {**GOOD, "themes": ["ui_ux"] * 4},
        {**GOOD, "themes": []},
        {**GOOD, "sentiment": "happy"},
        {**GOOD, "is_actionable": "yes"},
        {k: v for k, v in GOOD.items() if k != "sentiment"},
    ):
        with pytest.raises(ValueError):
            validate_tag(bad)


def test_taxonomy_is_v1():
    assert len(TAXONOMY) == 17 and "other" in TAXONOMY and "hinglish_code_switching" in TAXONOMY


def test_payload_never_contains_contacts():
    p = json.dumps(build_payload("k0", "Mail a@b.com, +91 98765 43210, @someone, https://x.co/y, www.z.com"))
    for bad in ("a@b.com", "98765", "@someone", "https://", "www."):
        assert bad not in p


def test_dry_run_makes_no_calls_and_estimates_cost():
    calls = []
    out = tag_reviews(df_reviews(), client=lambda payload: calls.append(payload), run=False)
    assert calls == [] and out["dry_run"] is True and out["n_to_tag"] == 10
    assert estimate_cost(10)["input_tokens"] > 0


def test_run_requires_client_and_flag():
    with pytest.raises(RuntimeError):
        tag_reviews(df_reviews(), client=None, run=True)


def test_cache_hit_skips_api_and_key_includes_version(tmp_path):
    calls = []

    def client(payload):
        calls.append(payload)
        return json.dumps(GOOD)

    cache = Cache(tmp_path / "c.json")
    df = df_reviews(3)
    tag_reviews(df, client=client, run=True, cache=cache, model="m1")
    assert len(calls) == 3
    tag_reviews(df, client=client, run=True, cache=cache, model="m1")
    assert len(calls) == 3  # all cached
    tag_reviews(df, client=client, run=True, cache=cache, model="m2")
    assert len(calls) == 6  # new model -> new key
    assert Cache.key("k0", PROMPT_VERSION, "m1") != Cache.key("k0", "v2", "m1")


def test_invalid_json_is_retried_then_succeeds(tmp_path):
    seq = iter(["not json", json.dumps({"themes": ["x"]}), json.dumps(GOOD)])
    out = tag_reviews(df_reviews(1), client=lambda p: next(seq), run=True,
                      cache=Cache(tmp_path / "c.json"), model="m")
    assert out["tags"]["k0"] == GOOD


def pool():
    rows = []
    for store, country in [("play", "unscoped"), ("appstore", "in"), ("appstore", "us")]:
        for rating in range(1, 6):
            for lang, cnt in [("en", 30), ("roman-Hindi", 3), ("Devanagari", 1)]:
                for i in range(cnt):
                    rows.append({"review_key": f"{store}{country}{rating}{lang}{i}", "store": store,
                                 "country": country, "rating": rating, "lang_detected": lang,
                                 "text_clean": f"review {store} {rating} {lang} {i}"})
    return pd.DataFrame(rows)


def test_sampler_hits_all_strata_no_oversampling_and_reproducible():
    df = pool()
    s1, counts = stratified_sample(df, 100, seed=7)
    s2, _ = stratified_sample(df, 100, seed=7)
    assert len(s1) == 100 and list(s1.review_key) == list(s2.review_key)
    assert s1.review_key.is_unique
    assert counts["n_strata_available"] == counts["n_strata_sampled"]
    for c in counts["strata"]:
        assert c["sampled"] <= c["available"]
    # Devanagari stratum has 1 available per cell: never more than 1 taken
    assert all(c["sampled"] <= 1 for c in counts["strata"] if c["lang_detected"] == "Devanagari")


def test_split_40_60_reproducible():
    s, _ = stratified_sample(pool(), 100, seed=7)
    a = split_dev_test(s, seed=7)
    b = split_dev_test(s, seed=7)
    assert (a.split == "dev").sum() == 40 and (a.split == "test").sum() == 60
    assert list(a.split) == list(b.split)


def test_gold_files_blind(tmp_path):
    blind, key, _counts = make_gold_files(pool(), tmp_path, seed=7)
    b = pd.read_csv(blind)
    assert len(b) == 100
    assert set(b.columns) == {"gold_id", "text", "themes", "sentiment", "mentions_competitor", "is_actionable"}
    assert b[["themes", "sentiment", "mentions_competitor", "is_actionable"]].isna().all().all()
    k = pd.read_csv(key)
    assert set(k.columns) >= {"gold_id", "review_key", "split", "store", "country", "rating", "lang_detected"}
    assert not any("pred" in c or "model" in c for c in b.columns)
    assert (tmp_path / "gold_strata_counts.json").exists()


def test_prompt_versions_registry():
    from src.tagging.tagger import PROMPTS

    assert set(PROMPTS) >= {"v1", "v2", "v3"}
    assert len(set(PROMPTS.values())) == len(PROMPTS)  # each revision actually differs
    p1 = build_payload("k", "x", version="v1")
    p2 = build_payload("k", "x", version="v2")
    assert p1["prompt_version"] == "v1" and p2["prompt_version"] == "v2"
    assert p1["system"] != p2["system"]
    for v in PROMPTS.values():
        assert all(t in v for t in TAXONOMY)  # every version lists the full v1 taxonomy


def test_cache_separates_prompt_versions(tmp_path):
    calls = []

    def client(payload):
        calls.append(payload["prompt_version"])
        return json.dumps(GOOD)

    cache = Cache(tmp_path / "c.json")
    df = df_reviews(2)
    tag_reviews(df, client=client, run=True, cache=cache, model="m", prompt_version="v1")
    tag_reviews(df, client=client, run=True, cache=cache, model="m", prompt_version="v2")
    assert calls == ["v1", "v1", "v2", "v2"]
