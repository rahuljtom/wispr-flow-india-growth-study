"""Google Play listing facts for competitor candidates (India storefront, public listing pages).

The unofficial google-play-scraper is used at low volume; every pull is logged. Install counts on Play
are GLOBAL bands, not India-specific. Prices are the listing's in-app item range in INR.
"""
import json
import re
import time
from pathlib import Path

import pandas as pd

from src.common.logs import append_failure, append_pull

CANDIDATES = {
    "ai.getsupernova.superflow": "Superflow",
    "com.google.android.inputmethod.latin": "Gboard",
    "com.typeless.mobile": "Typeless",
    "com.aquavoice.android": "Aqua Voice",
    "com.touchtalent.bobbleapp": "Bobble AI Keyboard",
    "info.hindime.voice.typing": "Hindi Voice Typing (HinKhoj)",
    "com.innosq.soundtypeai": "SoundType AI",
    "com.wispr.flowapp": "Wispr Flow (reference)",
}
RAW = Path("data/raw/competitors_play_raw.json")
OUT = Path("data/interim/competitor_play_stats.csv")


def pull():
    from google_play_scraper import app

    raw, rows = {}, []
    for pid, name in CANDIDATES.items():
        try:
            a = app(pid, lang="en", country="in")
        except Exception as e:  # noqa: BLE001 - logged, other candidates continue
            append_failure(f"play-competitor-{pid}", repr(e), 1, False)
            continue
        time.sleep(1.5)
        raw[pid] = {k: (v if isinstance(v, (str, int, float, bool, list, type(None))) else str(v))
                    for k, v in a.items() if k not in ("screenshots", "comments", "histogram")}
        d = (a.get("description") or "") + " " + (a.get("summary") or "")
        rows.append({
            "app_id": pid, "name": name, "title": a["title"], "developer": a["developer"],
            "installs_band_global": a["installs"], "min_installs": a.get("minInstalls"),
            "rating": round(a["score"], 2) if a.get("score") else "", "ratings_count": a.get("ratings"),
            "released": a.get("released") or "", "updated": str(a.get("lastUpdatedOn") or ""),
            "free": a.get("free"), "iap_range_inr": a.get("inAppProductPrice") or "",
            "ad_supported": a.get("adSupported"),
            "desc_mentions_hindi": bool(re.search(r"hindi|हिन्दी|हिंदी", d, re.IGNORECASE)),
            "desc_mentions_hinglish": bool(re.search(r"hinglish", d, re.IGNORECASE)),
            "desc_mentions_codeswitch": bool(re.search(r"code-?switch", d, re.IGNORECASE)),
            "desc_mentions_dictation": bool(re.search(r"dictat|voice typ|speech.to.text|voice.to.text", d, re.IGNORECASE)),
            "play_url": f"https://play.google.com/store/apps/details?id={pid}&hl=en_IN&gl=IN",
            "retrieved_on": time.strftime("%Y-%m-%d")})
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, default=str))
    append_pull("play-competitors", "google-play-scraper (unofficial)", "app() details, country=in",
                {"ids": list(CANDIDATES)}, RAW, rows=len(rows))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    return OUT


if __name__ == "__main__":
    print(pull())
