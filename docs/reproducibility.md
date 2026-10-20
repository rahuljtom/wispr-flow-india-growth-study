# Reproducibility

## What can be regenerated, and from what
| Tier | What | Inputs | Command | Network / keys |
|---|---|---|---|---|
| 1 | Decomposition, Trends event study, experiment sizing, price ladder, competitor matrix, charts, dashboard tables and workbook, per-page build guides, the deck | Files in this repository (`data/interim/trends_*.csv`, `data/interim/competitor_play_stats.csv`, `data/processed/*`, ledger, eval JSONs) | `make reproduce` | None |
| 2 | Raw acquisition: reviews, Trends, pricing snapshots, competitor listings | Public endpoints | Commands below | Network; Google Play and Trends are unofficial endpoints that rate-limit and change; the review salt in `.env` |
| 3 | Review tagging, gold set, evaluation, theme tables | Review text and gold labels, which are **not distributed** | Commands below | Network, `GEMINI_API_KEY`, explicit approval flag, and your own labels |

Tier 1 reproduces every number in the deck and dashboard except the review-theme tables and tagger metrics, which are committed as aggregates (`data/processed/themes_by_segment.csv`, `themes_monthly.csv`, `sentiment_overall.csv`, `a1_coverage.json`, `data/interim/eval_*.json`). Those cannot be re-derived without the private review text and labels; a reviewer with their own pull would obtain different review keys (the hashing salt is private) and a different review set, because the sources are live.

**Curated inputs (not generated):** `data/ledger/numbers_ledger.csv` (every reported figure with its source), `ASSUMPTIONS.md`, `data/processed/offers.csv` and `competitor_pricing.csv` (read from vendor pages, with URLs and dates). Re-check them against the cited sources rather than regenerating them.

## Setup
Python 3.12 is what the project was run on (3.11+ expected to work).
```bash
make setup                   # python3 -m venv .venv && pip install -r requirements.txt
make check                   # tests, ruff, number-to-ledger check, deck layout estimate
make reproduce               # tier 1 regeneration followed by the checks
```
`make reproduce` rewrites files under `data/processed`, `outputs/` and `docs/looker/`; `git diff` shows what changed. The deck's file timestamp changes on every build; compare slide text, not bytes.

## Environment variables (`.env`, never committed; template in `.env.example`)
| Variable | Needed for |
|---|---|
| `HASH_SALT` | Hashing review IDs (any random string; keep it private) |
| `GEMINI_API_KEY` | Real tagging calls (a free key is available from Google AI Studio) |
| `GEMINI_MODEL`, `GEMINI_RPM`, `GEMINI_RPD` | Optional overrides of the model ID and client-side rate limits |

## Tier 2: raw acquisition (writes to ignored `data/raw` and `data/private`)
```bash
python -m src.transform.run_wispr_reviews            # Play and App Store reviews -> scrubbed table + coverage
python -m src.pulls.trends "wispr flow" "voice typing"   # repeat for "whisper flow", "wisper flow", "whispr flow"
python -m src.pulls.pricing_snapshots                 # Wayback snapshots of the Wispr pricing page
python -m src.pulls.pricing_snapshots --parse         # snapshots -> data/processed/pricing_snapshots.csv
python -m src.pulls.competitor_play                   # competitor Play listing facts
python -m src.common.seed_ledger                      # re-seeds ledger rows R-001 to R-004 only
```
Every pull is logged in `data/logs/pull_log.csv` (and failures in `failure_log.csv`) with a SHA-256 of the raw file.

## Tier 3: tagging and evaluation (needs review text, labels, key and approval)
```bash
python -m src.tagging.gold                            # blind gold files (refuses to overwrite existing ones)
# label data/private/gold_blind.csv by hand (guide: docs/label_guide.md) and save it as gold_labels.csv
python -m src.tagging.tagger --gold-split dev --prompt-version v3 --name dev_v3            # dry run: prints payload and cost estimate
python -m src.tagging.tagger --gold-split dev --prompt-version v3 --name dev_v3 --run --approve-gemini-data-processing
python -m src.tagging.evaluate eval dev data/interim/tags/dev_v3.json
python -m src.tagging.evaluate freeze --model gemini-3.5-flash-lite --prompt-version v3
python -m src.tagging.tagger --gold-split test --prompt-version v3 --name test_v3 --run --approve-gemini-data-processing
python -m src.tagging.evaluate eval test data/interim/tags/test_v3.json      # allowed once
python -m src.tagging.bulk                            # seeded 600-review sample of non-gold reviews
python -m src.tagging.tagger --keys-file data/interim/bulk_sample_ids.csv --prompt-version v3 --name bulk_v3 --run --approve-gemini-data-processing
make themes   # same as: python -m src.analysis.run_a1 --partial (needs private data)
python -m src.analysis.run_a1 [--partial]             # theme tables and chart (--partial: analyse an interrupted run)
```
The first tagging call sends scrubbed review text to Google (see `docs/sources.md`). The free tier has a daily request limit that interrupted the bulk run at 321 of 600 reviews; analyses of that interim snapshot are labelled as such.

## Dashboard and presentation
- `make dashboard` regenerates the eleven dashboard CSVs, the workbook and the per-page guides; `make deck` builds `outputs/deck/deck.pptx`.
- The Looker Studio report is **not** created automatically: build it by hand from `docs/looker_studio_setup.md` (or the per-page guides in `docs/looker/`) in a Google account. The README links the published report; no Google Sheet or credential is part of this repository.

## Checks
`make check` runs the full pytest suite (CSV/schema rules, workbook round trip, independent recomputation of review shares, test metrics, decomposition and experiment sizes, competitor-score invariants, regression tests for corrected defects), ruff, the ledger check (every number in the deck and chart sidecars has a ledger row) and a text-fit estimate for the deck. Tests that need private data (gold files, review text, tags) skip when those files are absent.
