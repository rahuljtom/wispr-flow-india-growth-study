"""A1 on the bulk-tagged sample (frozen v3). Describes the sample only; not all users.

Language proxy: roman-Hindi/Devanagari text is a heuristic language flag, NOT geography.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.analysis.themes import MIN_N, theme_table

CAMPAIGN = pd.Timestamp("2026-04-27", tz="UTC")  # provisional (DECISIONS #3)


def load(tags_path="data/interim/tags/bulk_v3.json"):
    tags = json.loads(Path(tags_path).read_text())
    df = pd.read_csv("data/processed/wispr_reviews.csv", parse_dates=["review_date"])
    df = df[df["review_key"].isin(tags)].copy()
    df["themes"] = df["review_key"].map(lambda k: tags[k]["themes"])
    df["sentiment"] = df["review_key"].map(lambda k: tags[k]["sentiment"])
    df["lang_proxy"] = df["lang_detected"].map(
        lambda x: "roman-Hindi/Devanagari (language proxy)" if x in ("roman-Hindi", "Devanagari")
        else "en/other")
    return df


def partial_tags_from_cache(cache="data/interim/tag_cache.json", ids="data/interim/bulk_sample_ids.csv",
                            frozen="data/interim/frozen_config.json", out="data/interim/tags/bulk_v3_partial.json"):
    """Collect the cached tags of the frozen model and prompt for the selected bulk sample (an interrupted run)."""
    cfg = json.loads(Path(frozen).read_text())
    suffix = f"|{cfg['prompt_version']}|{cfg['model_id']}"
    sample = set(pd.read_csv(ids)["review_key"])
    tags = {k[: -len(suffix)]: v for k, v in json.loads(Path(cache).read_text()).items()
            if k.endswith(suffix) and k[: -len(suffix)] in sample}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(tags))
    return Path(out)


def main(tags_path="data/interim/tags/bulk_v3.json", partial_of=None):
    df = load(tags_path)
    cov = {"tagged": len(df), "sample": partial_of or len(df), "complete": partial_of is None,
           "by_store": {k: int(v) for k, v in df.groupby("store").size().items()},
           "date_min": str(df.review_date.min().date()), "date_max": str(df.review_date.max().date())}
    Path("data/processed/a1_coverage.json").write_text(json.dumps(cov, indent=1))
    segs = {"all tagged sample": df}
    segs["rating<=2 (low-rated)"] = df[df["rating"] <= 2]
    for st, g in df.groupby("store"):
        segs[f"store={st}"] = g
    for lp, g in df.groupby("lang_proxy"):
        segs[lp] = g
    for (st, c), g in df.groupby(["store", "country"]):
        if st == "appstore":
            segs[f"appstore {c} (not comparable windows)"] = g
    table = pd.concat([theme_table(g, name) for name, g in segs.items()], ignore_index=True)
    table.to_csv("data/processed/themes_by_segment.csv", index=False)
    sent = df.groupby("sentiment").size().rename("n").reset_index()
    sent["share"] = sent["n"] / len(df)
    sent.to_csv("data/processed/sentiment_overall.csv", index=False)
    df["month"] = df["review_date"].dt.strftime("%Y-%m")
    monthly = []
    for m, g in df.groupby("month"):
        monthly.append(theme_table(g, f"month={m}"))
    mt = pd.concat(monthly, ignore_index=True)
    mt.to_csv("data/processed/themes_monthly.csv", index=False)
    allt = table[(table.segment == "all tagged sample") & (table.n_with_theme > 0)].sort_values(
        "share", ascending=False).head(8)
    low = table[table.segment == "rating<=2 (low-rated)"].set_index("theme")
    n_all, n_low = int(allt.n_segment.iloc[0]), int(low.n_segment.iloc[0])
    order = list(allt.theme)[::-1]
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    ypos = range(len(order))
    h = 0.38
    a_idx = allt.set_index("theme")
    ax.barh([y + h / 2 for y in ypos], [a_idx.loc[t, "share"] * 100 for t in order], height=h, color="#3b6ea8",
            label=f"All tagged (n={n_all})",
            xerr=[[(a_idx.loc[t, "share"] - a_idx.loc[t, "ci_lo"]) * 100 for t in order],
                  [(a_idx.loc[t, "ci_hi"] - a_idx.loc[t, "share"]) * 100 for t in order]], capsize=2)
    if n_low >= MIN_N:
        ax.barh([y - h / 2 for y in ypos], [low.loc[t, "share"] * 100 for t in order], height=h, color="#e07b39",
                label=f"1-2 star reviews (n={n_low})",
                xerr=[[(low.loc[t, "share"] - low.loc[t, "ci_lo"]) * 100 for t in order],
                      [(low.loc[t, "ci_hi"] - low.loc[t, "share"]) * 100 for t in order]], capsize=2)
    ax.set_yticks(list(ypos))
    ax.set_yticklabels([t.replace("_", " ") for t in order])
    ax.set_xlim(0, None)
    ax.set_xlabel("% of reviews carrying the theme (Wilson 95% interval)")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_title("Review themes, interim sample (321 of 600 selected; newest Play reviews)", fontsize=10)
    fig.tight_layout()
    fig.savefig("outputs/charts/themes_overall_vs_low_rated.png", dpi=200)
    plt.close(fig)
    Path("outputs/charts/themes_overall_vs_low_rated.json").write_text(
        json.dumps({"labels": [str(n_all), str(n_low), "600"]}))
    top = allt
    print(len(df), "tagged rows joined; min cell n", MIN_N)
    print(top[["theme", "n_with_theme", "share", "ci_lo", "ci_hi", "mean_rating"]].round(3).to_string(index=False))
    print(table[table.segment.str.contains("proxy|store=")].groupby("segment").n_segment.first())


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--partial":
        # interrupted bulk run: analyse the stored partial snapshot (rebuilt from the cache only on request,
        # so a still-running tagging job cannot silently change published numbers)
        if "--refresh-partial" in sys.argv:
            partial_tags_from_cache()
        main("data/interim/tags/bulk_v3_partial.json", partial_of=600)
    else:
        main()
