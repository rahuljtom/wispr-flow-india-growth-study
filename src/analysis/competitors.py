"""Competitor matrix with a written rubric (scores 0-3; "unknown" when no sourced evidence).

Evidence used: Google Play listing facts pulled for the India storefront (install bands are GLOBAL),
plus the P1 research on vendor pricing pages and press. Claims are advertised by the developer, not tested.

Rubric
- android_in_india: 3 listing retrievable on the India Play storefront and updated or released in the last
  180 days; 2 listed but older; unknown if not found (absence from a search is not proof).
- hinglish_support: 3 explicit Hinglish or code-switching dictation claim; 2 explicit Hindi dictation without
  code-switching; 1 generic multilingual claim or Hindi/Hinglish text input only; unknown otherwise.
- reach_global_play: global Play install band: 3 at least 100M; 2 at least 1M; 1 at least 100k; 0 below 100k.
  India's share of installs is not public, so India-specific reach stays unknown.
- price_relevance (pressure on Flow's India pricing): 3 core dictation free (Play listing free with no in-app
  purchases) or an explicit per-month price at or below Flow's India monthly equivalent (320 INR, billed
  annually); 2 a documented free tier with a substantial allowance; 1 an explicit per-month list price above
  320 INR. Play in-app item ranges do NOT state billing periods (monthly, yearly or one-time), so they are never
  compared with Flow's price: unknown unless the vendor states the period.
- feature_overlap: 3 AI dictation that works across other apps with cleanup; 2 voice typing across apps without
  AI cleanup claims, or AI dictation in a single app; 1 voice input as a side feature or file transcription.
"""
import re
from datetime import date

import pandas as pd

FLOW_INDIA_MONTHLY_EQUIV_INR = 320  # R-071: India page, billed annually
NOW = date(2026, 10, 19)
STATS = "data/interim/competitor_play_stats.csv"
CRITERIA = ["android_in_india", "hinglish_support", "reach_global_play", "price_relevance", "feature_overlap"]


def reach_score(min_installs):
    if min_installs is None or pd.isna(min_installs):
        return None
    n = float(min_installs)
    return 3 if n >= 100_000_000 else 2 if n >= 1_000_000 else 1 if n >= 100_000 else 0


def parse_inr_range(text):
    if not isinstance(text, str) or not text.strip():
        return None
    nums = [float(x.replace(",", "")) for x in re.findall(r"₹\s*([\d,]+(?:\.\d+)?)", text)]
    return (min(nums), max(nums)) if nums else None


def price_score(kind, monthly_inr=None):
    """kind: 'free_core', 'free_tier' or 'explicit' (explicit per-month price with a stated billing period)."""
    if kind == "free_core":
        return 3
    if kind == "free_tier":
        return 2
    if kind == "explicit" and monthly_inr is not None:
        return 3 if monthly_inr <= FLOW_INDIA_MONTHLY_EQUIV_INR else 1
    return None


def android_score(listed, updated_days_ago):
    if not listed:
        return None
    return 3 if updated_days_ago is not None and updated_days_ago <= 180 else 2


def _days_ago(updated, released):
    for txt in (updated, released):
        try:
            return (NOW - pd.to_datetime(txt).date()).days
        except (ValueError, TypeError):
            continue
    return None


# Qualitative evidence curated from the listings and P1 research: (score, source, rationale)
HINGLISH = {
    "Superflow": (3, "play", "Listing claims Hinglish and code-switching, and dictation from Hindi and four other Indian languages to English"),
    "Gboard": (2, "play", "Listing lists Hindi among voice typing languages; code-switching is reported for the Gemini feature (TechCrunch 2026-05-12)"),
    "Hindi Voice Typing (HinKhoj)": (2, "play", "Hindi voice typing for messages and notes; no Hinglish or code-switching claim"),
    "Bobble AI Keyboard": (1, "play", "Hindi keyboard with Hinglish text input; the listing does not state voice-typing languages"),
    "SoundType AI": (1, "play", "Generic claim of 90 languages; Hindi not named"),
    "Typeless": (1, "https://www.typeless.com/pricing", "Pricing page claims 100+ languages; Hindi and Hinglish not named"),
    "Superwhisper": (1, "https://superwhisper.com", "Home page claims 100+ languages and dialects; Hindi not named"),
}
FEATURE = {
    "Superflow": (3, "Voice keyboard via Android Accessibility that works in other apps; Indian-language speech is output as English text (translation), unlike Flow's Hinglish transcription; claims accents and code-switching"),
    "Typeless": (3, "AI dictation, filler-word removal, works in every app (Play listing)"),
    "Aqua Voice": (3, "Speech to text in every app with voice editing and custom dictionary (Play listing and pricing page)"),
    "Gboard": (2, "Voice typing across apps; AI cleanup is announced for the Gemini feature but not rolled out to all devices"),
    "Superwhisper": (2, "Voice to text in any app with custom prompts; Android listing not found on the India storefront"),
    "Hindi Voice Typing (HinKhoj)": (2, "Voice typing in Hindi for SMS and messaging apps without AI cleanup"),
    "Bobble AI Keyboard": (1, "Keyboard (stickers, themes) with voice typing as a side feature"),
    "SoundType AI": (1, "Transcribes audio and video files; not an in-app dictation overlay"),
}
PRICE_EVIDENCE = {  # vendor-stated prices with a stated billing period (P1 research, USD at the implied 94.1 INR per USD)
    "Typeless": ("explicit", 12 * 94.1, "https://www.typeless.com/pricing",
                 "Pricing page: 12 USD per month billed yearly (about 1,129 INR a month) against Flow India 320 a month billed annually; Play INR items 3,250 to 15,700 have no stated billing period"),
    "Aqua Voice": ("explicit", 8 * 94.1, "https://aquavoice.com/pricing",
                   "Pricing page: 8 USD per month billed annually (about 753 INR a month) against Flow India 320; Play INR items 1,450 to 42,100 have no stated billing period"),
    "Superwhisper": ("free_tier", None, "https://superwhisper.com",
                     "Free tier with unlimited Whisper models and offline use; paid price rendering unclear on the page"),
}
OTHER = {  # candidates with no scoreable evidence, kept visible and unscored
    "Apple dictation": "Not researched; Apple dictation is iOS and macOS only and not on Google Play",
    "Google AI Edge Eloquent": "Free offline dictation app reported iOS-first (secondary press); no Google Play listing found",
}


def _row(comp, crit, score, url, why, when):
    return {"competitor": comp, "criterion": crit, "score": "unknown" if score is None else str(int(score)),
            "source_url": url if score is not None else "", "retrieved_on": when if score is not None else "",
            "rationale": why}


def build_matrix(stats_path=STATS):
    st = pd.read_csv(stats_path).set_index("name")
    rows = []
    for name in ["Superflow", "Gboard", "Typeless", "Aqua Voice", "Superwhisper", "Bobble AI Keyboard",
                 "Hindi Voice Typing (HinKhoj)", "SoundType AI"]:
        r = st.loc[name] if name in st.index else None
        url = r["play_url"] if r is not None else ""
        when = r["retrieved_on"] if r is not None else "2026-10-18"
        # android
        if r is not None:
            sc = android_score(True, _days_ago(r["updated"], r["released"]))
            why = f"Listing on the India Play storefront; updated {r['updated'] or 'n/a'}, released {r['released'] or 'n/a'}"
        else:
            sc, why = None, "No Google Play listing found by search on the India storefront; its site claims Android (not verified)"
        rows.append(_row(name, "android_in_india", sc, url, why, when))
        # hinglish
        h = HINGLISH.get(name)
        rows.append(_row(name, "hinglish_support", h[0] if h else None, (url if h and h[1] == "play" else h[1]) if h else "",
                         h[2] if h else "No Hindi or Hinglish statement found", when if h else ""))
        # reach
        if r is not None:
            rs = reach_score(r["min_installs"])
            rows.append(_row(name, "reach_global_play", rs, url,
                             f"Global Play install band {r['installs_band_global']} (India share not public); "
                             f"rating {r['rating']} from {int(r['ratings_count']) if pd.notna(r['ratings_count']) else 'few'} ratings", when))
        else:
            rows.append(_row(name, "reach_global_play", None, "", "No Play listing found, so no install band", ""))
        # price
        if name in PRICE_EVIDENCE:
            kind, monthly, purl, why = PRICE_EVIDENCE[name]
            rows.append(_row(name, "price_relevance", price_score(kind, monthly), purl, why, "2026-10-18"))
        elif r is not None:
            iap = parse_inr_range(r["iap_range_inr"] if pd.notna(r["iap_range_inr"]) else "")
            if iap is None and bool(r["free"]):
                rows.append(_row(name, "price_relevance", price_score("free_core"), url,
                                 "Play listing: free with no in-app purchases listed (core voice typing free)", when))
            else:
                rows.append(_row(name, "price_relevance", None, "",
                                 f"Play listing shows INR in-app items {iap[0]:,.0f} to {iap[1]:,.0f} per item without a billing period; "
                                 "no vendor price statement found, so not compared with Flow's price", ""))
        else:
            rows.append(_row(name, "price_relevance", None, "", "No price evidence", ""))
        # feature
        f = FEATURE.get(name)
        rows.append(_row(name, "feature_overlap", f[0] if f else None, url or "https://superwhisper.com" if f else "",
                         f[1] if f else "No evidence", when if f else ""))
    for name, why in OTHER.items():
        for c in CRITERIA:
            rows.append(_row(name, c, None, "", why, ""))
    return pd.DataFrame(rows)


def ranking(matrix):
    known = matrix[matrix.score != "unknown"].assign(s=lambda d: d.score.astype(int))
    g = known.groupby("competitor").s.agg(total="sum", known="count")
    out = pd.DataFrame({"competitor": sorted(set(matrix.competitor))}).set_index("competitor").join(g).fillna(0).astype(int)
    out["unknown"] = len(CRITERIA) - out["known"]
    out["min_possible"] = out["total"]
    out["max_possible"] = out["total"] + 3 * out["unknown"]
    return out.sort_values(["total", "known"], ascending=False).reset_index()


def leave_one_out(matrix):
    rows = []
    known = matrix[matrix.score != "unknown"].assign(s=lambda d: d.score.astype(int))
    for drop in [None, *CRITERIA]:
        k = known if drop is None else known[known.criterion != drop]
        tot = k.groupby("competitor").s.sum().sort_values(ascending=False)
        top = tot[tot == tot.iloc[0]].index.tolist()
        rows.append({"criterion_dropped": drop or "none", "leader(s)": "; ".join(top), "top_total": int(tot.iloc[0]),
                     "runner_up": tot.index[len(top)] if len(top) < len(tot) else "", })
    return pd.DataFrame(rows)


def main():
    m = build_matrix()
    m.to_csv("data/processed/competitor_matrix.csv", index=False)
    ranking(m).to_csv("data/processed/competitor_ranking.csv", index=False)
    leave_one_out(m).to_csv("data/processed/competitor_sensitivity.csv", index=False)
    print(ranking(m).to_string(index=False))
    print(leave_one_out(m).to_string(index=False))


if __name__ == "__main__":
    main()
