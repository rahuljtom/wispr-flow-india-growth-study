"""Seed ledger with the reported figures from ASSUMPTIONS.md and the TechCrunch article.

Verified against the fetched article on 2026-10-18 (P1).
"""
from src.common.ledger import add_claim, read_ledger

URL = "https://techcrunch.com/2026/05/09/voice-ai-in-india-is-hard-wispr-flow-is-betting-on-it-anyway/"
TITLE = "Voice AI in India is hard. Wispr Flow is betting on it anyway (TechCrunch, Sensor Tower data)"
ROWS = [
    ("R-001", "Global downloads Oct 2025-Apr 2026", 2500000, "installs"),
    ("R-002", "India install share", 14, "%"),
    ("R-003", "India in-app revenue share", 2, "%"),
    ("R-004", "India price, annual plan, per month", 320, "INR"),
]


def main():
    have = {r["claim_id"] for r in read_ledger()}
    for cid, label, value, unit in ROWS:
        if cid not in have:
            add_claim(cid, "slide 2", label, value, unit, "reported", source_url=URL,
                      source_title=TITLE, source_date="2026-05-09", retrieved_on="2026-10-18",
                      date_range="2025-10/2026-04" if cid != "R-004" else "from 2025-12",
                      caveat="IAP only; 'more than' 2.5M; India pricing year not stated in text"
                      if cid != "R-004" else "Article gives month (December) but not year")


if __name__ == "__main__":
    main()
