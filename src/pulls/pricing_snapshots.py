"""Wayback snapshots of pricing pages (raw HTML to data/raw, every fetch logged)."""
import csv
import html
import re
import time
from pathlib import Path

import requests

from src.common.logs import append_pull
from src.pulls.reviews import with_retries

RAW = Path("data/raw/pricing")


def list_snapshots(url, start="20251001"):
    r = requests.get("https://web.archive.org/cdx/search/cdx", timeout=60, params={
        "url": url, "from": start, "output": "json", "filter": "statuscode:200",
        "collapse": "timestamp:6", "fl": "timestamp,original,digest"})
    r.raise_for_status()
    return [dict(zip(r.json()[0], row)) for row in r.json()[1:]]


def fetch_snapshot(slug, snap):
    pid = f"wayback-{slug}-{snap['timestamp']}"
    archive_url = f"https://web.archive.org/web/{snap['timestamp']}id_/{snap['original']}"

    def get():
        r = requests.get(archive_url, timeout=60)
        r.raise_for_status()
        return r.content

    body = with_retries(pid, get, sleep=time.sleep)
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{slug}_{snap['timestamp']}.html"
    path.write_bytes(body)
    append_pull(pid, "wayback machine", archive_url, {"timestamp": snap["timestamp"]}, path,
                rows=1)
    return path, archive_url


USD_TOKEN = re.compile(r"\$\s?\d{1,2}(?:\.\d+)?\s?/\s?(?:user\s?/\s?)?mo(?:nth)?")
FREE_LIMIT = re.compile(r"[\d,]+ words per week[^.]{0,30}")


def parse_snapshots(raw_dir=RAW, out="data/processed/pricing_snapshots.csv"):
    """Extract USD price tokens and the free-limit snippet from archived pricing pages (plan attribution not parsed)."""
    rows = []
    for f in sorted(Path(raw_dir).glob("wispr_*.html")):
        ts = re.search(r"_(\d{14})", f.name).group(1)
        h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", f.read_text(errors="ignore"), flags=re.DOTALL)
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))
        usd = sorted(set(USD_TOKEN.findall(text)))  # spacing variants are kept distinct, then normalised below
        free = FREE_LIMIT.findall(text)
        rows.append({
            "snapshot_utc": ts, "archive_url": f"https://web.archive.org/web/{ts}id_/https://wisprflow.ai/pricing",
            "usd_per_month_tokens": "; ".join(x.replace(" ", "") for x in usd),
            "free_limit_snippet": free[0].strip() if free else "not found",
            "inr_price_present": str("₹" in text or "INR" in text).lower(),
            "note": "Plan attribution of tokens not parsed; archive crawler pages show USD only"})
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return Path(out)


if __name__ == "__main__":
    import sys

    if "--parse" in sys.argv:
        print(parse_snapshots())
    else:
        for s in list_snapshots("wisprflow.ai/pricing"):
            print(fetch_snapshot("wispr", s))
            time.sleep(2)
