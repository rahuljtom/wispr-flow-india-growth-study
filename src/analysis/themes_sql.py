"""Theme shares by segment, computed by sql/segments_*.sql and sql/theme_stats.sql.

Python only prepares the inputs (a reviews table, a long review-theme table and the taxonomy) and
passes MIN_N and Z as parameters. The output has the columns of themes.theme_table.
"""
import pandas as pd

from src.analysis.themes import MIN_N, Z
from src.common.sql import run_sql
from src.tagging.tagger import TAXONOMY

COLUMNS = ["segment", "theme", "n_segment", "n_with_theme", "share", "ci_lo", "ci_hi", "mean_rating",
           "suppressed"]


def inputs(df):
    """df: one row per tagged review with review_key, rating, store, country, lang_proxy,
    review_date (UTC) and themes (list)."""
    reviews = pd.DataFrame({
        "review_key": df["review_key"].astype(str), "rating": df["rating"].astype(float),
        "store": df["store"].astype(str), "country": df["country"].astype(str),
        "lang_proxy": df["lang_proxy"].astype(str),
        "month": pd.to_datetime(df["review_date"]).dt.strftime("%Y-%m")})
    themes = pd.DataFrame(
        [(k, t) for k, ts in zip(reviews["review_key"], df["themes"], strict=True) for t in set(ts)],
        columns=["review_key", "theme"])
    taxonomy = pd.DataFrame({"theme": TAXONOMY, "ord": range(len(TAXONOMY))})
    return reviews, themes, taxonomy


def _stats(segments_file, reviews, themes, taxonomy):
    members = run_sql(segments_file, tables={"reviews": reviews})
    out = run_sql("theme_stats.sql", {"min_n": MIN_N, "z": Z},
                  {"segment_members": members, "reviews": reviews, "review_themes": themes,
                   "taxonomy": taxonomy})
    return out[COLUMNS].astype({"n_segment": "int64", "n_with_theme": "int64", "suppressed": "bool"})


def theme_tables(df):
    """Return (overall, monthly) theme tables for the tagged reviews in df."""
    reviews, themes, taxonomy = inputs(df)
    return (_stats("segments_overall.sql", reviews, themes, taxonomy),
            _stats("segments_monthly.sql", reviews, themes, taxonomy))
