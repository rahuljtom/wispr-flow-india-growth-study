import pandas as pd

from src.tagging.bulk import select_sample


def pool():
    rows = []
    for store, n in (("play", 400), ("appstore", 80)):
        for i in range(n):
            rows.append({"review_key": f"{store}{i}", "store": store, "country": "x", "rating": i % 5 + 1,
                         "lang_detected": "roman-Hindi" if i % 50 == 0 else "en", "text_clean": "some text"})
    return pd.DataFrame(rows)


def test_excludes_gold_reproducible_and_counts():
    df = pool()
    gold = set(df.review_key.iloc[:30]) | {"appstore3", "appstore4"}
    s1, c1 = select_sample(df, gold, 100, seed=11)
    s2, _ = select_sample(df, gold, 100, seed=11)
    assert list(s1.review_key) == list(s2.review_key) and len(s1) == 100
    assert not (set(s1.review_key) & gold) and s1.review_key.is_unique
    assert c1["n_sampled"] == 100 and c1["seed"] == 11
    assert sum(c1["by_store"].values()) == 100 and set(c1["by_rating"]) == {"1", "2", "3", "4", "5"}
    assert "by_language" in c1
    for cell in c1["strata"]:
        assert cell["sampled"] <= cell["available"]
    # proportional to the non-gold pool (no oversampling of small strata)
    play = c1["by_store"]["play"] / 100
    assert abs(play - (400 - len(gold & set(df[df.store == "play"].review_key))) / (480 - len(gold))) < 0.03


def test_different_seed_differs():
    df = pool()
    a, _ = select_sample(df, set(), 100, seed=1)
    b, _ = select_sample(df, set(), 100, seed=2)
    assert list(a.review_key) != list(b.review_key)
