# Validation and corrections log

## What is checked automatically (`make check`)
| Check | What it covers |
|---|---|
| `pytest` | CSV and workbook rules (UTF-8, headers, ragged rows, blank-not-zero, unknown-not-zero); ledger and pull-log rules; review scrubbing and hashing; tagger dry run, caching, schema validation and approval gates; evaluation freeze guards (test split scored once); decomposition, sizing and Trends logic including known-effect and not-estimable cases; competitor rubric; data-dictionary coverage of every dashboard column; generated per-page guides match the master guide |
| Independent recomputation (`tests/test_independent_audit.py`, `tests/test_deck_numbers.py`) | Review shares and Wilson intervals, monthly counts, test-split micro-F1 and kappa, decomposition ratios, experiment sample sizes (pooled-variance formula agrees with the arcsine method within 7%) and durations, competitor reach scores recomputed from Play facts, and ledger values against recomputation. Tests that need private data skip when it is absent |
| SQL equivalence (`tests/test_sql_*.py`) | Each SQL query is compared with the earlier pandas implementation on the committed tables and on synthetic data (suppressed cells stay blank, unknown prices stay NULL, ties round to even, repeated themes count once). With private data present, the interim theme tables are also compared byte for byte with the committed files |
| `ruff` | Style and common defects in `src/` and `tests/` |
| Ledger check (`src.common.check_ledger`) | Every number on a deck slide or chart sidecar has a ledger row (claim IDs, years and ISO dates are ignored) |
| Layout check (`src.deck.layout_check`) | Text-fit and overlap estimate for the deck; it is an estimate, not a rendering |

## Not verified
- The deck's rendered appearance (no renderer was available): open it in PowerPoint once.
- The Looker Studio build guide against the live product: it was written from Google's documentation. Menu names may differ by version, and the guide gives fallbacks.
- India-specific reach, tested Hinglish accuracy, billing periods of Play in-app items, payment-method availability and offer redeemability (all marked unverified or unknown in the data).

## Corrections made during review
| Area | Defect found | Correction |
|---|---|---|
| Competitor scoring | An early score compared Google Play in-app item ranges (no billing period) with Flow's annual price, which made Superflow look like the primary competitor (14 of 15) | Price relevance now uses only vendor-stated per-month prices or documented free access; Play ranges are "unknown" (Superflow 11 on four known criteria, Gboard 13); regression tests added |
| Competitor claim | An earlier statement that no competitor could be named reflected thin research (hand-picked candidates, unknown reach) | Candidates found through a Google Play India search and scored with a written rubric; India reach replaced by global Play installs because India's share is not public |
| Slide wording | A slide called Gboard the free default that "sets the price anchor" although its price was not sourced; another said two criteria were unknown for every product | Reworded to what the evidence supports |
| Experiments | Durations ignored follow-up windows; kill criteria were truncated and vague | Follow-up days and total days added; decision rules written in full; E3's unit mismatch flagged |
| Slides | The language-proxy statement ("too few reviews") was wrong (none of the tagged reviews were in it); the largest theme, "other", was silently left out of the headline | Both stated on the slide |
| Evaluation | Gold rows left blank by the labeller were scored as errors | Excluded and counted (`n_unlabelled_gold`), applied to every version and the test split |
| Gold labels | One development review had four themes (cap is three); one generic-praise label contradicted the stated convention | Corrected in the development split only, with a backup and rationale (`docs/annotation_audit.md`); test labels unchanged |
| Price chart | Labels said "annual", which reads like an annual price | "billed annually" / "billed monthly"; only prices with stated periods are charted |
| Dashboard data | One File Upload dataset cannot hold CSVs with different headers; formulas and chart filters in the first design caused display failures | One workbook with a worksheet per table; derived fields precomputed in the data; cross-filtering switched off; guide rewritten |
| Documents | The research brief still listed the Play package and App Store ID as unverified; the evaluation report mixed superseded and current numbers | Brief updated (IDs verified); evaluation report rewritten from the current result files |
| Publication hygiene | Working notes, tool-specific rules and project-management files were tracked | Removed from the published scope (kept locally, ignored); decision log and guides reworded; deck and workbook metadata set explicitly |

## Interim-data note
The bulk review tagging was interrupted by the free-tier daily limit at 321 of 600 selected reviews. A later request tagged one more review; the published outputs deliberately keep the 321-review snapshot (verified identical to the committed theme tables), and all review results are labelled interim.
