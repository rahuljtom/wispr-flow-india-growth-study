# Research brief (sources retrieved 2026-10-18 and 2026-10-19)

Public proxies only; no internal Wispr data. Status chips follow docs/ledger_schema.md.

## A. Wispr facts
| Item | Finding | Status | Source |
|---|---|---|---|
| Sensor Tower window figures | 2.5M+ global downloads, India 14% of installs (#2 after US), ~2% of in-app purchase revenue, Oct 2025-Apr 2026 | reported | TechCrunch 2026-05-09 |
| India price | Rs 320/month on annual plans, introduced December (year not stated in article text) | reported | TechCrunch |
| Global price | Pro $12/mo billed annually, $15 monthly; Growth and Enterprise tiers exist | reported | wisprflow.ai/pricing |
| Free tier | 2,000 words/week desktop, 1,000/week mobile (iOS/Android) on the fetched pricing page | reported | wisprflow.ai/pricing |
| Android free tier / launch promo | Launch-era (2026-02-23): free with no usage cap during early access, no end date (9to5Google). Current official docs (help articles, 'last updated 1 day ago', 2026-10-18) put Android under the Free-plan caps: iOS and Android share one pool, soft cap 1,000 and hard cap 1,500 words a week; desktop soft 2,000 and hard 5,000 (R-007, R-008, R-080, R-081). No unlimited Android promotion is documented now, and no official end announcement was found. The India page's 'free ... with unlimited dictation' appears to be marketing copy at odds with the docs and with its own line that Pro removes the weekly limit (inference, not proven). E2 is redefined as a cap-level test | launch-era free/unlimited: reported secondary; ended-status inferred from docs, not announced (R-009) | docs.wisprflow.ai; 9to5Google; wisprflow.ai/india |
| India pricing | India page (2026-10-18): Rs 400/user/month monthly; Rs 320/user/month billed annually (annual charge Rs 3,840 is derived arithmetic, not displayed). The general pricing page shows USD only | reported primary (R-070, R-071); derived (R-072) | wisprflow.ai/india |
| Android launch | 2026-02-23, 'early rollout'/'early access' (TechCrunch and 9to5Google, both published that day). A different milestone from the India launch announcement | reported, secondary (R-073) | TechCrunch; 9to5Google |
| Android requirements | Android 13+; microphone, display-over-apps and accessibility permissions are mandatory; battery exemption optional | reported | docs.wisprflow.ai |
| Hinglish | Earliest public report: TechCrunch 2026-02-23 describes the Hinglish model as already released, alongside the Android launch (early rollout to select users), with a CEO quote that it transcribes Hinglish rather than output Hindi script (WeRSM: Latin script). That is press reporting, not a Wispr release note, and does not prove general availability that day (R-089). The internal development date is unknown (R-090). TechCrunch 2026-05-09 says beta testing earlier in 2026. ET (2026-04-28 IST) says the India launch introduced 'full Hinglish support' | reported (secondary); general availability date and development date UNVERIFIED | TechCrunch; WeRSM; ET |
| India launch / campaign date | ET (archive capture 2026-04-27 18:59 UTC; article 2026-04-28 IST): official India launch 'on Monday' (2026-04-27, day inferred), and a CEO LinkedIn post that Monday saying the autos were live in Bengaluru. So 2026-04-27 is both the reported India launch date and a documented live date for the campaign (R-079, R-091), but a start before that Monday is not excluded and the LinkedIn post was not read. Media4Growth (2026-04-29) gives no start date | reported secondary | ET; Media4Growth |
| India checkout methods | India page FAQ: UPI and cards (Visa, Mastercard, American Express, Discover); the sentence 'You can also pay via ___ for faster checkout' has an empty blank in the rendered text and DOM, so the third option is unnamed and Net Banking is unsupported as the answer (R-084). Wispr docs: Wispr-billed plans use Stripe's billing portal, store plans use Apple or Google Play (R-085); no doc lists UPI or net banking. Google Play Help (India): UPI is supported for subscriptions via UPI Autopay (R-082) and net banking is discontinued from October 2025 (R-083); whether Wispr's Play subscription offers UPI is UNVERIFIED. Advertised, not tested | reported (advertised / general Google capability); Wispr-specific route UNVERIFIED | wisprflow.ai/india; docs.wisprflow.ai; support.google.com |
| Play package | com.wispr.flowapp: the Google Play listing resolves to "Wispr Flow: AI Voice-to-Text" (Wispr AI, Inc.) | verified (DECISIONS #15) | play.google.com |
| App Store ID | 6497229487: the iTunes lookup resolves to the same app | verified (DECISIONS #15) | itunes.apple.com lookup |
| Company-reported | India growth ~60% MoM before, ~100% after the campaign; India ~50:50 desktop/mobile | reported by company | TechCrunch |

## B. Competitors (re-audited 2026-10-19)
**Method.** Candidates came from a search of the India Google Play storefront plus the competitor list recorded in DECISIONS #4; facts come from each public listing (`src/pulls/competitor_play.py`) and, where the vendor states them, pricing pages. Scores 0 to 3 follow one rubric (`src/analysis/competitors.py`); "unknown" when nothing sourced. Limits: Play install bands are **global**, not India; Hinglish and feature claims are developer-advertised and untested; Play in-app item ranges do **not state billing periods**, so they are never compared with Flow's price (an earlier version compared item prices with Flow's annual charge; that was an error and has been removed).

| Candidate | Known criteria | Total (of 15) | Possible range | Key evidence |
|---|---|---|---|---|
| **Gboard** | 5 | **13** | 13 | Free, no in-app purchases, 10B+ installs, Hindi voice typing; AI cleanup announced (Rambler) but device-limited |
| Hindi Voice Typing (HinKhoj) | 5 | 11 | 11 | Free with ads, Hindi voice typing, 500K+ installs; not AI dictation |
| **Superflow** (Android, released 2026-03-25) | 4 | **11** | 11 to 14 | Listing: Hinglish and code-switching, voice keyboard via Accessibility, Indian-language speech output as English, 1M+ installs, rating 4.62; INR items 250 to 950 with no stated period, so price unknown; developer is a Bengaluru-registered company whose site never mentions Superflow |
| Typeless | 5 | 9 | 9 | AI dictation in every app, 500K+ installs; 12 USD a month billed yearly (about 1,129 INR a month, 3.5 times Flow India) |
| Aqua Voice | 4 | 7 | 7 to 10 | Android listing new (2026-10-06), 1K+ installs; 8 USD a month billed annually |
| Bobble AI Keyboard (India) | 4 | 7 | 7 to 10 | 50M+ installs, Hinglish keyboard, voice typing a side feature |
| SoundType AI | 4 | 7 | 7 to 10 | File transcription, 1M+ installs |
| Superwhisper | 3 | 5 | 5 to 11 | Android listing not found on the India storefront |
| Apple dictation, Google AI Edge Eloquent | 0 | n/a | 0 to 15 | Not on Google Play; unscored |

**Reading (judgement, not a measurement).** *Most dangerous substitute: Gboard* (highest known total, a free default with the largest reach). *Closest dedicated dictation rival: Superflow*, because even at its floor (11) it beats Typeless's maximum (9) and every other dedicated AI-dictation app; its price is unknown, so it could reach 14. Dropping any single criterion keeps Gboard first except when price is dropped (Superflow first) or reach is dropped (Gboard ties HinKhoj), so the Gboard-versus-Superflow order is not robust; `data/processed/competitor_sensitivity.csv`. Evidence that would change this: India-specific installs and revenue, tested Hinglish accuracy, Superflow's billing periods and pricing page.
**Added candidates.** Superflow, Bobble AI Keyboard, HinKhoj Hindi Voice Typing and SoundType AI were not in the original list in DECISIONS #4 and were added from the store search. Soniox was dropped (no verifiable India-relevant evidence).
**Wispr's own Play listing** shows INR items from 400 to 3,849 with no billing period; the India page lists 400 monthly and 320 a month billed annually (3,840 a year). The Play listing proves INR billing exists on Google Play, not which payment methods are accepted.
**Company claim that conflicts with the 2% figure.** The company told ETtech India is its second-largest base by users and paying subscribers; with 2% of in-app revenue that points to much India revenue billed outside the app stores (hypothesis).

## A2. Offers and promotions (verified 2026-10-18; see data/processed/offers.csv)
Standard free tier is not the same as promotional Pro access.
| Offer | Stated benefit | Redemption / restrictions as documented | Status |
|---|---|---|---|
| Zepto partner offer | 3 months of Flow Pro | Browser claim with code on the Zepto page (rendered page re-read 2026-10-18: a search snippet saying past subscribers are excluded did not match the page; fully ended subscriptions do not block); payment info may be requested at checkout, charges nothing in the trial, renews and bills unless cancelled (the page calls the no-card and auto-return terms unconfirmed; R-086); individual plans only; student accounts and accounts created in the iOS/Android app excluded; one promotion per account; no absolute date or expiry; activation up to 48 hours; billing after trial unless cancelled; desktop (Mac/Windows) | reported (R-074); current redeemability UNVERIFIED; not Android-specific |
| CRED partner offer | 10 months in the title; body says trial length is the days the code grants (1-365) | Browser claim; payment details required at checkout, no charge until the trial ends, then bills unless cancelled (R-087); individual plans only; active App Store/Google Play subscription blocks redemption; expiry varies by campaign; desktop code entry | reported (R-075); length per code and redeemability UNVERIFIED; not Android-specific |
| Students and educators | Help doc on weekly limits: the Student plan has no weekly limit (Pro, Pro Trial, Growth, Enterprise likewise), so 'free student plan with unlimited dictation' is supported for eligible accounts. Students page: free plan stays free, 50% off Pro, 3 months Pro free for new Pro students (R-076, R-077). Help doc: no universal rate, per-account terms set by support, one educator case got 40% (R-078), some student accounts may get an annual $0 Student plan | .edu or supported domain recognised automatically, otherwise proof submitted to support | ambiguous on rate and eligibility: the offers above are distinct and are not combined; the X post (IndianIdle) was inaccessible (HTTP 402) and is no longer cited, official pages cover the same ground |
Neither partner offer is shown as available to every Indian user, and the help articles are not proof that either offer is redeemable today (R-088). A search result titled 'CRED and Zepto Mobile Promotion' (docs article 8590963041) returns 404 and is not in the Billing & Plans collection; it is not used. Nothing here is evidence about how promotions affect observed revenue.

## Rejected source
zackproser.com Android review: describes a voice-notes product with a $19/month plan, which does not match Wispr Flow; not cited.

## C. India Android share / voice-typing behaviour
Not verified in this pass. No credible source fetched. Android share stays a 30/50/70% scenario assumption.

## Open items
The exact start of the Bengaluru campaign, whether the added competitors belong in the final list, the Trends control states (provisional), and every UNVERIFIED row above.
