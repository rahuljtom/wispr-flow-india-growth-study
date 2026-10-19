import datetime as dt

import pandas as pd
import pytest

from src.transform.reviews import (
    build_table,
    detect_lang,
    hash_key,
    parse_appstore,
    parse_play,
    scrub_text,
)

PLAY = [
    {"reviewId": "gp-1", "userName": "Asha Rao", "content": "Great app, mail me asha@x.com or +91 98765 43210",
     "score": 5, "thumbsUpCount": 2, "reviewCreatedVersion": "1.4.1",
     "at": dt.datetime(2026, 4, 27, 17, 0), "replyContent": "Thanks", "repliedAt": dt.datetime(2026, 4, 28)},
    {"reviewId": "gp-1", "userName": "Asha Rao", "content": "dup", "score": 5, "thumbsUpCount": 0,
     "reviewCreatedVersion": None, "at": dt.datetime(2026, 4, 27, 17, 0), "replyContent": None,
     "repliedAt": None},
    {"reviewId": "gp-2", "userName": "Bob", "content": "bahut accha hai lekin nahi chal raha",
     "score": 3, "thumbsUpCount": 0, "reviewCreatedVersion": "1.4.0",
     "at": dt.datetime(2026, 4, 1), "replyContent": None, "repliedAt": None},
    {"reviewId": "gp-bad", "userName": "X", "content": "bad rating", "score": 9, "thumbsUpCount": 0,
     "reviewCreatedVersion": None, "at": dt.datetime(2026, 4, 1), "replyContent": None,
     "repliedAt": None},
    {"userName": "NoId"},  # malformed
]

APPSTORE = {"feed": {"entry": [
    {"id": {"label": "as-1"}, "author": {"name": {"label": "Priya"}}, "im:rating": {"label": "4"},
     "title": {"label": "Nice"}, "content": {"label": "Works @priya_x see https://a.com/b"},
     "im:version": {"label": "2.1"}, "updated": {"label": "2026-04-27T10:00:00-07:00"}},
    {"id": {"label": "as-bad"}},  # malformed
]}}


def test_scrub_removes_contacts():
    t = scrub_text("a@b.co call +91 98765 43210 or 022-2345-6789 @handle http://x.y/z www.q.com")
    for bad in ("a@b.co", "98765", "2345", "@handle", "http", "www."):
        assert bad not in t


def test_scrub_keeps_normal_text():
    assert scrub_text("Rated 5 stars, version 1.4.1 is great") == "Rated 5 stars, version 1.4.1 is great"


def test_lang_heuristic():
    assert detect_lang("यह ऐप बहुत अच्छा है") == "Devanagari"
    assert detect_lang("bahut accha hai, nahi chalta") == "roman-Hindi"
    assert detect_lang("This works great on my phone") == "en"
    assert detect_lang("这个应用很好") == "other"


def test_hash_stable_and_salted():
    assert hash_key("s", "a", "gp-1") == hash_key("s", "a", "gp-1")
    assert hash_key("s1", "a", "gp-1") != hash_key("s2", "a", "gp-1")
    with pytest.raises(ValueError):
        hash_key("", "a", "x")


def test_play_parse_skips_malformed_and_converts_utc():
    recs = parse_play(PLAY, "in")
    assert len(recs) == 4  # record without reviewId dropped; bad rating dropped in build_table
    assert recs[0]["review_date"] == pd.Timestamp("2026-04-27T17:00:00", tz="UTC")


def test_appstore_timezone_to_utc():
    recs = parse_appstore(APPSTORE, "in")
    assert len(recs) == 1
    assert recs[0]["review_date"] == pd.Timestamp("2026-04-27T17:00:00", tz="UTC")


def test_build_table_dedupe_rating_scrub_and_reconcile():
    recs = parse_play(PLAY, "in") + parse_appstore(APPSTORE, "in")
    priv, pub, stats = build_table(recs, app="wispr", store_by_source={"play": "play", "appstore": "appstore"}, salt="s")
    assert len(pub) == 3  # gp-1, gp-2, as-1 (dup and bad rating removed)
    assert stats["input_rows"] == 4 + 1 and stats["dropped_dupes"] == 1 and stats["dropped_bad_rating"] == 1
    assert stats["input_rows"] - stats["dropped_dupes"] - stats["dropped_bad_rating"] == len(pub)
    assert pub["rating"].between(1, 5).all()
    assert "user_name" not in pub.columns and "text_raw" not in pub.columns
    joined = " ".join(pub["text_clean"])
    for bad in ("asha@x.com", "98765", "@priya_x", "https://"):
        assert bad not in joined
    assert "Asha" not in joined
    assert "user_name" in priv.columns or "text_raw" in priv.columns
    assert set(pub["lang_detected"]) <= {"en", "roman-Hindi", "Devanagari", "other"}
    assert pub.loc[pub.review_key == hash_key("s", "wispr", "gp-1"), "has_dev_reply"].iloc[0]


def test_empty_input_ok():
    _priv, pub, stats = build_table([], "wispr", {}, "s")
    assert len(pub) == 0 and stats["input_rows"] == 0
