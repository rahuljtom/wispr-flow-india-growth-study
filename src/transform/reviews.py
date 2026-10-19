"""Review parsing, scrubbing and table building (rules 2, 8).

Language heuristic (documented): Devanagari if >=30% of letters are Devanagari; roman-Hindi if
the text is mostly ASCII and contains >=2 distinct common Hinglish function words; en if mostly
ASCII otherwise; other for everything else.
"""
import hashlib
import re

import pandas as pd

LANGS = {"en", "roman-Hindi", "Devanagari", "other"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
HANDLE = re.compile(r"(?<![\w])@\w{2,}")
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{6,}\d)(?!\w)")
HINGLISH = {
    "hai", "hain", "nahi", "nahin", "bahut", "accha", "acha", "achha", "kya", "bhi", "mein", "me",
    "ko", "ke", "ki", "ka", "hota", "karo", "karna", "bilkul", "lekin", "aur", "toh", "yeh", "ye",
    "mera", "kaam", "raha", "rahi", "chalta", "chal", "bekar", "zabardast",
}
HINGLISH_STRONG = HINGLISH - {"me", "ko", "ke", "ki", "ka", "ye", "chal", "aur", "mera"}


def scrub_text(text):
    text = EMAIL.sub("[email]", text or "")
    text = URL.sub("[url]", text)
    text = HANDLE.sub("[handle]", text)
    text = PHONE.sub(lambda m: "[phone]" if sum(c.isdigit() for c in m.group()) >= 7 else m.group(), text)
    return text


def detect_lang(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "other"
    deva = sum("ऀ" <= c <= "ॿ" for c in letters)
    if deva / len(letters) >= 0.3:
        return "Devanagari"
    ascii_share = sum(c.isascii() for c in letters) / len(letters)
    if ascii_share < 0.7:
        return "other"
    words = set(re.findall(r"[a-z]+", text.lower()))
    if len(words & HINGLISH_STRONG) >= 2:
        return "roman-Hindi"
    return "en"


def hash_key(salt, app, source_id):
    if not salt:
        raise ValueError("HASH_SALT must be set")
    return hashlib.sha256(f"{salt}|{app}|{source_id}".encode()).hexdigest()[:24]


def _utc(ts):
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def parse_play(rows, country):
    out = []
    for r in rows:
        try:
            out.append({
                "source": "play", "source_id": r["reviewId"], "country": country,
                "rating": r["score"], "text_raw": r.get("content") or "",
                "user_name": r.get("userName") or "", "review_date": _utc(r["at"]),
                "app_version": r.get("reviewCreatedVersion"), "thumbs_up": r.get("thumbsUpCount", 0),
                "has_dev_reply": bool(r.get("replyContent")),
            })
        except (KeyError, ValueError, TypeError):
            continue
    return out


def parse_appstore(payload, country):
    out = []
    entries = payload.get("feed", {}).get("entry", []) if isinstance(payload, dict) else []
    if isinstance(entries, dict):
        entries = [entries]
    for e in entries:
        try:
            title = e.get("title", {}).get("label", "")
            body = e["content"]["label"]
            out.append({
                "source": "appstore", "source_id": e["id"]["label"], "country": country,
                "rating": int(e["im:rating"]["label"]),
                "text_raw": f"{title}. {body}" if title else body,
                "user_name": e.get("author", {}).get("name", {}).get("label", ""),
                "review_date": _utc(e["updated"]["label"]),
                "app_version": e.get("im:version", {}).get("label"), "thumbs_up": 0,
                "has_dev_reply": False,
            })
        except (KeyError, ValueError, TypeError, AttributeError):
            continue
    return out


PUB_COLS = ["review_key", "app", "store", "country", "rating", "text_clean", "review_date",
            "app_version", "thumbs_up", "has_dev_reply", "lang_detected"]


def build_table(records, app, store_by_source, salt):
    """Returns (private, public, stats). Private keeps raw text; public never does."""
    stats = {"input_rows": len(records), "dropped_dupes": 0, "dropped_bad_rating": 0}
    rows, seen = [], set()
    for r in records:
        key = hash_key(salt, app, r["source_id"])
        if key in seen:
            stats["dropped_dupes"] += 1
            continue
        seen.add(key)
        if not isinstance(r["rating"], int) or not 1 <= r["rating"] <= 5:
            stats["dropped_bad_rating"] += 1
            continue
        clean = scrub_text(r["text_raw"])
        name = (r["user_name"] or "").strip()
        if len(name) >= 3:
            clean = re.sub(re.escape(name), "[name]", clean, flags=re.IGNORECASE)
        rows.append({
            "review_key": key, "app": app, "store": store_by_source.get(r["source"], r["source"]),
            "country": r["country"], "rating": r["rating"], "text_clean": clean,
            "review_date": r["review_date"], "app_version": r["app_version"],
            "thumbs_up": r["thumbs_up"], "has_dev_reply": r["has_dev_reply"],
            "lang_detected": detect_lang(clean), "text_raw": r["text_raw"],
            "user_name": r["user_name"],
        })
    priv = pd.DataFrame(rows, columns=PUB_COLS + ["text_raw", "user_name"])
    return priv, priv[PUB_COLS].copy(), stats


def coverage_report(pub, min_months=6):
    """Markdown coverage table per app/store/country (docs/coverage.md)."""
    lines = ["| app | store | country | n | min date | max date | n per month | warning |",
             "|---|---|---|---|---|---|---|---|"]
    for (app, store, country), g in pub.groupby(["app", "store", "country"]):
        d = g["review_date"]
        per_month = d.dt.strftime("%Y-%m").value_counts().sort_index()
        months = "; ".join(f"{m}: {n}" for m, n in per_month.items())
        span = (d.max().year - d.min().year) * 12 + d.max().month - d.min().month + 1
        warn = f"shallow history ({span} months)" if span < min_months else ""
        lines.append(f"| {app} | {store} | {country} | {len(g)} | {d.min():%Y-%m-%d} | "
                     f"{d.max():%Y-%m-%d} | {months} | {warn} |")
    return "\n".join(lines) + "\n"
