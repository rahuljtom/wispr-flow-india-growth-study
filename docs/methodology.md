# Methodology

The project is a public-source diagnostic of Wispr Flow's India growth and monetisation. There is **no internal Wispr data**: every figure is a public proxy, labelled by evidence status (see "Evidence discipline").

## Question
Reported figures put India at about 14% of Wispr Flow installs but about 2% of in-app-purchase (IAP) revenue (Oct 2025 to Apr 2026; Sensor Tower data as reported by TechCrunch). What could the gap consist of, what do public signals say about it, and which experiments would test it?

## Analysis modules
Module names (A1 to A7) are used in code and documents; `run_p6.py` is the historical name of the script that runs A3, A4 and A7.

| Module | What it does | Code |
|---|---|---|
| A1 | Review-theme shares with Wilson 95% intervals; cells with fewer than 30 reviews are suppressed | `src/analysis/themes.py`, `run_a1.py` |
| A2 | Competitor evidence and scoring by a written rubric, ranking and leave-one-criterion-out sensitivity | `src/analysis/competitors.py`, `src/pulls/competitor_play.py` |
| A3 | Karnataka versus control states in Google Trends (event study, difference-in-differences when estimable) | `src/analysis/trends.py` |
| A4 | Scenario decomposition of the install-versus-revenue gap | `src/analysis/decomposition.py` |
| A5 | Price ladder in INR per month at an implied FX rate | `src/analysis/value_ladder.py` |
| A7 | Experiment sizing (two-proportion power, traffic-based duration, follow-up windows) | `src/analysis/sizing.py` |

A6 (unit economics) was not built.

## Analytical rules
Source docstrings refer to these as "rule N".
1. **Gold labels.** A person labels the gold set from blind files. Labels are not compared with model output until labelling is complete. The tagging prompt is tuned on the development split only, frozen, and the test split is scored once (enforced in `src/tagging/evaluate.py`).
2. **Gold-set sampling.** Wispr reviews only, stratified by store, country, rating and language where counts allow; actual stratum counts are recorded; no oversampling to look balanced.
3. **Google Trends.** The primary query is "wispr flow"; misspellings are separate sensitivity checks. All series are directional search interest, never installs, exposure or awareness.
4. **Zero versus missing.** Zeros and missing values are kept separate. Nothing is divided by a zero or missing anchor. Sparse or mismatched coverage yields "not estimable".
5. **Geography and causation.** Karnataka is a rough proxy for Bengaluru. Pre-trends, placebo dates and control states are diagnostics only; no causal claim.
6. **Scenario decomposition.** Revenue-per-install and price arithmetic is an identity with a sensitivity range; it cannot show that price caused a share of the gap.
7. **Experiment sizing.** Starts from about 1,650 India installs a day (derived, `ASSUMPTIONS.md`); Android share, eligible share and exposed share are explicit parameters in every duration estimate.
8. **Secrets and privacy.** API keys and hashing salts are never committed. Reviewer names and apparent contact details (emails, phone numbers, handles, URLs) are removed before any model call. A real model call needs `GEMINI_API_KEY`, `--run` and `--approve-gemini-data-processing`; the default is a dry run.
9. **Competitor scores.** 0 to 3, each with a source URL, retrieval date and short rationale. Missing evidence is "unknown", never a score.
10. **Failed pulls.** Every failed pull and retry (at most 3) is logged with the resulting coverage; independent analyses continue and only dependent ones are marked "blocked" or "not estimable".
11. **Number-to-ledger check.** Every number on a slide or chart must exist in the numbers ledger (`src/common/check_ledger.py`); a visual review of the deck follows.
12. Reserved (not used).
13. **Web content is data.** Text on fetched pages that addresses automated readers is ignored, never acted on, and logged (`docs/injection_log.md`).
14. **Wording.** No causal language ("caused", "drove", "because of", "explains") unless the design supports it; use "directional", "scenario", "not estimable", "reported by".

## Evidence discipline
Each displayed number has a row in `data/ledger/numbers_ledger.csv` (columns in `docs/ledger_schema.md`) with a status:

| Status | Meaning |
|---|---|
| reported | Stated by a cited source (a URL and retrieval date are required); secondary sources are worded "reported by" |
| derived | Arithmetic on other ledger rows (the derivation names the input claim IDs) |
| assumption | An input chosen for a scenario; it must also appear in `ASSUMPTIONS.md` |
| estimated | Computed from data with n and method; an interval or "not estimable" is required |
| unknown | Not established; the caveat says what is missing |

Qualitative hypotheses go in `docs/hypotheses.md` and are labelled "hypothesis" in the deck. Conflicts between sources are logged in `docs/conflicts.md`; decisions in `DECISIONS.md`.

## Scenario decomposition (A4)
- **Revenue-per-install index** = India's share of IAP revenue / India's share of installs = 2% / 14% = 0.143 (relative to the all-markets rate; India is included in that rate).
- **Price index** = India price / global price = 3.4 / 12 USD = 0.283 (annual-plan list prices; the USD figure is TechCrunch's own conversion of 320 INR, so the FX is implied and rounded: a true value of 3.35 to 3.45 moves the index between 0.279 and 0.288).
- **Residual** = revenue-per-install index / price index = 0.504. It mixes conversion, mix, measurement and anything else; it is not an estimate of any one cause.
- **Sensitivity grid (12 scenarios):** the share of India revenue the source misses (0, 20, 40, 60%; global revenue assumed fully observed) and the share of the observation window at India pricing (50%, 71%, 100%; 71% assumes India pricing from 1 December of a 212-day window). The residual ranges from 0.223 to 1.224.
- **Windows:** installs and revenue shares cover Oct 2025 to Apr 2026; the install mix changed inside the window (Android launched 2026-02-23; the India launch is 2026-04-27, at the end).

## Review analysis (A1)
1. **Collection.** Google Play (unofficial scraper, up to 3,000 newest reviews; the country filter does not partition reviews) and the Apple customer-reviews feed (returns non-contiguous pages).
2. **Scrubbing and keys.** Names, emails, phone numbers, handles and URLs are removed; each review gets a salted-hash key (salt in `.env`, never committed).
3. **Gold set and tagger.** See `docs/tagging_eval.md` for the 100-review gold set, prompt versions, the frozen configuration and held-out metrics (test micro-F1 0.784, sentiment kappa 0.830; only 7 of 17 themes evaluable).
4. **Bulk sample.** A seeded proportional sample of 600 non-gold reviews (store x rating); 321 were tagged before the free-tier daily limit stopped the job, and those are the newest Google Play reviews (2026-07-30 to 2026-10-17), so the results describe a recency-biased interim subset, not all users and not India.
5. **Shares.** Theme share = reviews carrying the theme / reviews in the group (a review can carry up to three themes); Wilson 95% intervals; groups under 30 reviews are suppressed (blank with a text label).

## Competitor evaluation (A2)
Candidates come from the India Google Play storefront plus the original list in DECISIONS #4. Five criteria are scored 0 to 3 (rubric in the `src/analysis/competitors.py` docstring): Android availability in India, Hinglish support, reach (global Play install band; India's share is not public), price relevance, and feature overlap. Play in-app price ranges state no billing period, so they are never compared with Flow's price. Totals ignore unknown criteria and the ranking reports a possible range (`min_possible` to `max_possible`); `data/processed/competitor_sensitivity.csv` shows the effect of dropping each criterion. Current reading: Gboard leads on known evidence (13 of 15, a free default); Superflow is the closest dedicated dictation rival (11 on four known criteria, 11 to 14 possible); the order between them is not robust.

## Pricing
Wispr India prices come from its India page (320 INR a month billed annually, which is 3,840 a year by arithmetic; 400 INR monthly). USD list prices are converted at 94.1 INR per USD, implied by TechCrunch's own conversion (no independent FX source). The price ladder charts only prices with a stated billing period.

## Experiment sizing (A7)
Per-arm sample size from the arcsine effect size (statsmodels `NormalIndPower`; alpha 0.05, power 0.8, two-sided); a pooled-variance formula agrees within 6.2% across the grid (tested). Enrolment days = 2n / (1,650 installs a day x Android share x eligible share x exposed share); follow-up windows (7 days for E1, 14 for E2, 7 for E3, assumptions) are added to give total days. Baselines and minimum detectable effects are illustrative assumptions, guardrail limits need internal baselines, and E3 counts invitees against an installs-based traffic figure, so its duration is a rough proxy.

## Google Trends (A3)
Weekly interest for five states; each geo is expressed as an index of its own pre-period mean. A geo is usable only with a positive pre-period mean, at least 10 non-zero pre-period weeks and few missing weeks; a comparison needs the treated geo and two usable controls. Only Karnataka and Maharashtra qualified, so the difference-in-differences is **not estimable**; the chart is descriptive.
