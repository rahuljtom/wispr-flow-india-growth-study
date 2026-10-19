"""Pull Wispr reviews (Play in/us, App Store in/us), transform, write tables and coverage."""
import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.pulls.reviews import pull_appstore, pull_play
from src.transform.reviews import build_table, coverage_report, parse_appstore, parse_play

PLAY_ID, APPSTORE_ID = "com.wispr.flowapp", "6497229487"


def main():
    load_dotenv()
    salt = os.environ["HASH_SALT"]
    recs = []
    # Play returned identical review sets for country=in and country=us (verified 2026-10-18),
    # so reviews are not country-partitioned: pull once and label the country "unscoped".
    rows, _ = pull_play(PLAY_ID, "in", "wispr")
    recs += parse_play(rows, "unscoped")
    for c in ("in", "us"):
        try:
            pages, _ = pull_appstore(APPSTORE_ID, c, "wispr")
            for pg in pages:
                recs += parse_appstore(pg, c)
        except Exception as e:  # noqa: BLE001
            print("appstore failed", c, e)
    priv, pub, stats = build_table(recs, "wispr", {"play": "play", "appstore": "appstore"}, salt)
    Path("data/private").mkdir(parents=True, exist_ok=True)
    priv.to_csv("data/private/wispr_reviews_private.csv", index=False)
    pub.to_csv("data/processed/wispr_reviews.csv", index=False)
    Path("docs/coverage.md").write_text(
        "# Coverage\n\n## Wispr reviews\n\n" + coverage_report(pub) + "\n```\n" + json.dumps(stats) + "\n```\n")
    print(stats, len(pub))
    print(pd.crosstab([pub.store, pub.country], pub.lang_detected))


if __name__ == "__main__":
    main()
