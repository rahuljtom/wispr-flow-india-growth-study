# Coverage

## Wispr reviews

| app | store | country | n | min date | max date | n per month | warning |
|---|---|---|---|---|---|---|---|
| wispr | appstore | in | 100 | 2025-09-22 | 2026-02-24 | 2025-09: 3; 2025-10: 10; 2025-11: 14; 2025-12: 39; 2026-01: 15; 2026-02: 19 |  |
| wispr | appstore | us | 100 | 2026-09-15 | 2026-10-08 | 2026-09: 50; 2026-10: 50 | shallow history (2 months) |
| wispr | play | unscoped | 3000 | 2026-03-20 | 2026-10-17 | 2026-03: 166; 2026-04: 505; 2026-05: 255; 2026-06: 183; 2026-07: 204; 2026-08: 456; 2026-09: 764; 2026-10: 467 |  |

```
{"input_rows": 3200, "dropped_dupes": 0, "dropped_bad_rating": 0}
```

## Findings that limit India-vs-US review analysis (2026-10-18)
- **Google Play:** `country=in` and `country=us` returned identical review IDs (checked on the 5 newest and on all 3,000). The scraper's reviews are not partitioned by country, so Play rows are labelled `unscoped`. India-vs-US on Play is **not estimable** from this source. Play history starts 2026-03-20 (3,000-review cap reached), so it does not cover the Dec 2025 India price change.
- **App Store RSS:** unreliable. Pages return 0 or 50 entries unpredictably, so coverage is non-contiguous and changes between runs (India: 100 reviews, 2025-09 to 2026-02; US: 100 to 150 reviews, Aug to Oct 2026, run-dependent). The India and US windows do not overlap, so a like-for-like comparison is **not estimable**.
- Language heuristic on Play: Devanagari 5, roman-Hindi 32, en 2,942, other 21 (of 3,000). A language-based India proxy would be a heuristic, not geography.

## Google Trends (weekly, 2025-09-07 to 2026-10-11 complete weeks; anchor 'voice typing')

Relative search interest only. Each query pulled with the anchor in one request per geo; values are normalised per request, so cross-geo comparison uses each geo's own pre-period mean.

| query | geo | weeks | target zero weeks | target missing | anchor zero weeks | target mean | anchor mean |
|---|---|---|---|---|---|---|---|
| wispr flow | IN-DL | 59 | 43 | 0 | 48 | 14.5 | 9.1 |
| wispr flow | IN-KA | 59 | 14 | 0 | 12 | 45.0 | 29.1 |
| wispr flow | IN-MH | 59 | 14 | 0 | 0 | 40.1 | 63.5 |
| wispr flow | IN-TG | 59 | 34 | 0 | 48 | 29.8 | 10.3 |
| wispr flow | IN-TN | 59 | 41 | 0 | 0 | 11.3 | 60.4 |
| whisper flow | IN-DL | 59 | 54 | 0 | 48 | 3.3 | 9.1 |
| whisper flow | IN-KA | 59 | 46 | 0 | 12 | 9.5 | 41.6 |
| whisper flow | IN-MH | 59 | 33 | 0 | 0 | 15.1 | 63.5 |
| whisper flow | IN-TG | 59 | 51 | 0 | 48 | 9.4 | 13.4 |
| whisper flow | IN-TN | 59 | 57 | 0 | 0 | 0.5 | 60.4 |
| wisper flow | IN-DL | 59 | 57 | 0 | 48 | 0.4 | 9.1 |
| wisper flow | IN-KA | 59 | 53 | 0 | 12 | 3.3 | 38.3 |
| wisper flow | IN-MH | 59 | 55 | 0 | 0 | 1.8 | 63.5 |
| wisper flow | IN-TG | 59 | 57 | 0 | 48 | 0.7 | 13.4 |
| wisper flow | IN-TN | 59 | 57 | 0 | 0 | 0.3 | 60.4 |
| whispr flow | IN-DL | 59 | 57 | 0 | 48 | 0.2 | 9.1 |
| whispr flow | IN-KA | 59 | 57 | 0 | 12 | 0.4 | 41.6 |
| whispr flow | IN-MH | 59 | 56 | 0 | 0 | 0.7 | 63.5 |
| whispr flow | IN-TG | 59 | 57 | 0 | 48 | 0.3 | 13.4 |
| whispr flow | IN-TN | 59 | 57 | 0 | 0 | 0.1 | 60.4 |

**Trends sparsity (rule 4):** the "voice typing" anchor is zero in 48 of 59 weeks for IN-DL and IN-TG and 12 of 59 for IN-KA, so ratio-to-anchor is computed only where the anchor is non-zero and non-missing. "wispr flow" itself is zero in 43 (DL), 34 (TG) and 41 (TN) of 59 weeks, so those controls are sparse; any geo whose pre-period mean is zero is "not estimable". Misspelling series are almost entirely zero outside IN-MH/IN-KA and are sensitivity checks only. Google returned one 429 (retried, resolved). The incomplete current week is dropped.

## Pricing snapshots
13 Wayback snapshots of wisprflow.ai/pricing (2025-10-09 to 2026-10-01), logged in pull_log. All show USD only: **no INR price ever appears on the archived public page**, so the December 2025 India price change is visible only via TechCrunch, not in these snapshots. The Wayback crawler's geography is unknown. Plan attribution of the extracted USD tokens is not parsed (some snapshots show $10/user/mo billed annually before $12 later; unattributed, not used). Competitor prices are USD only; no INR prices found for any competitor. Apple Dictation and Gboard pricing unknown.
