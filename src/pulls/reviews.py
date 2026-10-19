"""Review pulls (rule 10: max 3 retries, every failure logged)."""
import contextlib
import json
import time
import uuid
from pathlib import Path

import requests

from src.common.logs import MAX_RETRIES, append_failure, append_pull

RAW = Path("data/raw")


def with_retries(pull_id, fn, log_dir=Path("data/logs"), sleep=time.sleep):
    for attempt in range(MAX_RETRIES + 1):
        try:
            return fn()
        except Exception as e:
            if attempt == MAX_RETRIES:
                append_failure(pull_id, repr(e), MAX_RETRIES, False, log_dir=log_dir)
                raise
            append_failure(pull_id, repr(e), attempt + 1, False, log_dir=log_dir)
            sleep(2 ** attempt)


def pull_play(app_id, country, label, count=3000):
    from google_play_scraper import Sort, reviews

    pid = f"play-{label}-{country}-{uuid.uuid4().hex[:6]}"
    out, token = [], None

    def page():
        return reviews(app_id, lang="en", country=country, sort=Sort.NEWEST,
                       count=min(200, count - len(out)), continuation_token=token)

    while len(out) < count:
        batch, token = with_retries(pid, page)
        out += batch
        if not batch or token is None:
            break
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{pid}.json"
    path.write_text(json.dumps(out, default=str))
    append_pull(pid, "google-play-scraper (unofficial)", app_id,
                {"country": country, "lang": "en", "sort": "newest", "count": count},
                path, rows=len(out))
    return out, path


def pull_appstore(app_id, country, label, max_pages=10):
    """Apple's RSS endpoint is erratic: a page may return 0 entries on one call and 50 on the
    next, so an empty page is treated as a retryable failure (max 3) and later pages still run."""
    pid = f"appstore-{label}-{country}-{uuid.uuid4().hex[:6]}"
    pages = []
    for p in range(1, max_pages + 1):
        url = (f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}"
               f"/sortBy=mostRecent/page={p}/json")

        def get(url=url):
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            if not data.get("feed", {}).get("entry"):
                raise ValueError("empty page")
            return data

        with contextlib.suppress(Exception):  # failures are logged by with_retries
            pages.append(with_retries(pid, get))
        time.sleep(1)
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{pid}.json"
    path.write_text(json.dumps(pages))
    n = sum(len(pg["feed"]["entry"]) for pg in pages)
    append_pull(pid, "itunes rss customerreviews", app_id,
                {"country": country, "max_pages": max_pages}, path, rows=n,
                status="ok" if pages else "empty")
    return pages, path
