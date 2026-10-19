# Sources, provenance and terms of use

Every cited URL, retrieval date and per-source note is in `docs/source_log.md`; every displayed number is traced in `data/ledger/numbers_ledger.csv`. This page summarises the source types and what may and may not be redistributed.

| Source | Used for | How obtained | Redistribution in this repository |
|---|---|---|---|
| TechCrunch (2026-02-23, 2026-05-09, 2026-05-12), Economic Times (via an archive.org capture), 9to5Google, WeRSM, Media4Growth | Install and revenue shares (Sensor Tower data as reported), launch dates, India price, campaign, Hinglish and Gboard announcements | Read and paraphrased | Facts and short titles only; no article text. Raw captures stay outside the repository (`data/raw/`) |
| Wispr Flow website, India page, pricing page, students page, Help Center articles | Prices, free-tier caps, payment methods, offers, eligibility, Android requirements | Read and paraphrased | Facts and URLs only |
| Google Play listings (India storefront) | Competitor facts (install bands, ratings, release and update dates, in-app item ranges, descriptions) and review text | Public listing pages and reviews via the unofficial `google-play-scraper`, low volume with spacing and retries | Competitor listing facts only (`data/interim/competitor_play_stats.csv`). **Review text is not redistributed.** Google Play's terms restrict automated access; this use is limited research collection and reviewers should check the current terms before re-running |
| Apple customer-reviews feed (RSS/JSON) | Review text for the App Store | Public feed, erratic pages | Not redistributed |
| Google Trends (via the unofficial `pytrends`) | Weekly relative search interest for five Indian states | API calls, rate-limited, retried | Weekly relative values for five states are included (`data/interim/trends_*.csv`); they are aggregates, not personal data. Check Google's terms before reuse |
| Wayback Machine (archive.org) | Archived Wispr pricing pages; one archived news article | CDX API and captures | Derived table only (`data/processed/pricing_snapshots.csv`); raw captures stay in `data/raw/` |
| Google Gemini API (free tier) | Tagging scrubbed review text | API calls, only with explicit approval flags | Aggregate metrics and run records only. Google's unpaid-tier terms allow submitted content to be used to improve its products and reviewed by people; names, emails, phones, handles and URLs are removed beforehand |
| Google Play Help (India payment methods), Stripe and Google API documentation | Payment-method context, API behaviour | Read | Facts and URLs only |

## Notes
- **Secondary figures.** The 14% install share, the 2% in-app revenue share and the 2.5M download count are Sensor Tower figures reported by one article (TechCrunch, 2026-05-09); they are not verified independently.
- **Rejected source.** One third-party Android review was not cited because its content did not match the product (`docs/research_brief.md`).
- **Content safety.** Fetched pages were checked for text addressed to automated readers; none was found (`docs/injection_log.md`).
- **Licence of this repository.** No licence file is included yet; until the repository owner adds one, all rights are reserved by default. Third-party names and trademarks belong to their owners.
