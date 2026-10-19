# Wispr Flow India: a public-signals growth diagnostic

An evidence-ledgered analysis of why India is a large share of Wispr Flow's installs but a small share of its in-app-purchase (IAP) revenue, built only from public sources. It produces a scenario decomposition of the gap, a validated LLM review-tagging workflow, a sourced competitor and pricing comparison, experiment sizing sized to India traffic, a ten-slide deck, and the data and build guide for a ten-page Looker Studio dashboard.

> **There is no internal Wispr data.** Everything is a public proxy. Each number carries an evidence status (reported, derived, assumption, estimated, unknown); scenarios are not forecasts and nothing here establishes causation. See [Limitations](docs/limitations.md).

## The question
Sensor Tower data reported by TechCrunch puts India at about **14% of installs but about 2% of in-app-purchase revenue** (Oct 2025 to Apr 2026). What could the gap consist of, what do public signals say, and which experiments would test it? It matters because India is reported as the second-largest install market while Wispr launched India-specific pricing (320 INR a month on annual plans) and a Hinglish model.

## Findings, with status
| Finding | Value | Status |
|---|---|---|
| India share of installs / in-app purchase revenue, Oct 2025 to Apr 2026 | 14% / 2% | reported (Sensor Tower via TechCrunch, one secondary source; IAP only) |
| Revenue per install relative to the global rate | 0.143 | derived (2% / 14%) |
| Price index (India 3.4 USD vs global 12 USD, annual list prices, implied FX) | 0.283 | derived |
| Residual (conversion, mix, measurement, other) | 0.504; 0.223 to 1.224 across 12 scenarios | derived scenario; cannot be apportioned between price and other factors |
| Wispr India price | 320 INR a month billed annually (3,840 a year); 400 INR monthly | reported (India page); the annual total is arithmetic |
| Company claim: India is its second-largest base by users and paying subscribers | claim | reported by the company; with 2% of IAP revenue it suggests much India revenue is billed outside the app stores (hypothesis) |
| Review themes, interim sample of 321 newest Google Play reviews (all) | praise 28.7%, accuracy 21.5%, pricing 11.2% (other 31.5%) | estimated; not all users, not India-specific |
| One- and two-star reviews (n = 52) | pricing 26.9% vs 11.2% overall (intervals do not overlap) | estimated, directional |
| Tagger on the held-out test split (60 reviews, scored once) | micro-F1 0.784 (0.72 to 0.85); sentiment kappa 0.830 (0.68 to 0.95); 7 of 17 themes evaluable | estimated; one labeller |
| Competitors (rubric, five criteria) | Gboard 13 of 15 (free default; most dangerous substitute); Superflow 11 on four known criteria, 11 to 14 possible (closest dedicated dictation rival); Typeless 9 | derived from Play listings and developer claims; order between Gboard and Superflow not robust |
| Karnataka versus control states in Google Trends | not estimable (only 2 of 5 states had enough pre-period activity) | not estimable |
| Experiments (illustrative baselines) | E1 1,376 per arm, 10.0 to 29.2 days; E2 3,788, 22.2 to 75.2; E3 1,680, 9.5 to 15.1 (including follow-up) | assumptions plus calculation |

## How it works
```
public sources ──► pulls (src/pulls) ──► data/raw, data/private (not distributed)
                                   └──► scrub + hash ──► gold set + tagger (src/tagging) ──► themes, metrics
curated evidence ──► numbers ledger + ASSUMPTIONS ──► analysis A1-A7 (src/analysis)
                                                   └──► dashboard tables + workbook + deck (src/deck)
```
Methodology, rules and formulas: [docs/methodology.md](docs/methodology.md). Review-tagging evaluation: [docs/tagging_eval.md](docs/tagging_eval.md). Fields and null semantics (why `unknown` is not zero and how suppressed values appear): [docs/data_dictionary.md](docs/data_dictionary.md).

### Data and coverage
Sources, dates and terms: [docs/sources.md](docs/sources.md) and [docs/source_log.md](docs/source_log.md). Reviews: 3,000 Google Play reviews (2026-03 to 2026-10, not partitioned by country) and two partial App Store pages for India and US that do not overlap, so an India-versus-US comparison is not estimable; Google Trends weekly for five states (Sep 2025 to Oct 2026); archived Wispr pricing pages (13 snapshots); Google Play listings for the competitors; vendor pricing and documentation pages.

## Repository layout
```
src/analysis/      A1-A7 analysis modules (themes, competitors, trends, decomposition, value ladder, sizing, charts)
src/pulls/         Reviews, Trends, pricing snapshots and competitor listing pulls (rate-limited, logged)
src/transform/     Review parsing, scrubbing, hashing; price parser
src/tagging/       Gemini backend, tagger (dry run by default), gold set, bulk sample, evaluation with freeze guards
src/common/        Numbers ledger, ledger check, pull/failure logs
src/deck/          Deck, dashboard tables, workbook, layout check, per-page guide generator
tests/             pytest suite (schema rules, independent recomputation, regression tests)
data/ledger/       numbers_ledger.csv (every displayed number and its source or derivation)
data/processed/    Aggregated results and curated tables (no review text)
data/interim/      Trends series, competitor listing facts, evaluation results and run records
data/logs/         Pull and failure logs
outputs/           deck/deck.pptx, dashboard/ (CSVs + workbook), charts/
docs/              Methodology, data dictionary, sources, limitations, reproducibility, validation, research notes
```
Stack (from the imports): Python, pandas, numpy, scipy, statsmodels, matplotlib, python-pptx, openpyxl, requests, python-dotenv, google-play-scraper, pytrends, pytest and ruff; Google's Gemini API for tagging.

## Install, run, verify
```bash
make setup        # venv + dependencies (Python 3.12 used; 3.11+ expected to work)
make check        # pytest, ruff, number-to-ledger check on the deck, deck text-fit estimate
make reproduce    # regenerate everything that can be rebuilt from the repository, then check
```
`make reproduce` needs no network, key or private data. Raw acquisition and review tagging need network access, a free Gemini key and, for evaluation, your own labels; exact commands, environment variables and what cannot be reproduced are in [docs/reproducibility.md](docs/reproducibility.md). Copy `.env.example` to `.env` and fill in `HASH_SALT` (and `GEMINI_API_KEY` for tagging); never commit it.

### Verifying the results independently
`tests/test_independent_audit.py` recomputes review shares and Wilson intervals, the test-split F1 and kappa, the experiment sample sizes (a second formula) and the competitor reach scores with different code from the pipeline; `tests/test_deck_numbers.py` compares ledger values with recomputation; the ledger check fails if a number on a slide has no ledger row. Validation history and corrections: [docs/validation.md](docs/validation.md).

## Deliverables
- **Deck:** `outputs/deck/deck.pptx` (10 slides, generated; footnotes come from the ledger). Layout is checked by an estimate only, so open it once in PowerPoint before sharing.
- **Dashboard data:** `outputs/dashboard/` (eleven CSVs and `wispr_dashboard_data.xlsx`).
- **Looker Studio report:** built by hand from the workbook following [docs/looker_studio_setup.md](docs/looker_studio_setup.md) (per-page guides in `docs/looker/`). The report is a manual step in a Google account; this repository contains no report, link or Google Sheet.

## Limitations (summary)
Public proxies only; revenue is IAP only from one secondary source; the review sample is an interim, recency-biased subset; the gold set is small and single-labelled; competitor evidence is Play listings and developer claims; experiment baselines are illustrative. Full list: [docs/limitations.md](docs/limitations.md).

## Privacy, terms and licence
Review text, gold labels, hashed review IDs and raw pulls are not distributed; names, emails, phone numbers, handles and URLs are removed before any model call, and a real call needs an explicit flag. Source terms are noted in [docs/sources.md](docs/sources.md); Google Play and Google Trends are accessed through unofficial libraries, so check current terms before re-running. No licence file is included yet, so all rights are reserved by default until the repository owner adds one.
