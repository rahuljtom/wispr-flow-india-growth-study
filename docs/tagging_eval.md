# Review-tagging evaluation

An LLM assigns up to three themes, a sentiment, a competitor mention and an actionability flag to each review. This document records how the tagger was evaluated against a small human-labelled gold set, what was tuned, what was frozen, and what the held-out result is. Code: `src/tagging/`; labels and review text are private and not distributed (see `docs/data_dictionary.md`).

## Configuration and protocol
- **Backend:** Gemini API free tier (Interactions API), model ID `gemini-3.5-flash-lite`; JSON-schema output, validated and retried (at most 3 attempts); temperature not set because the API reference lists no such parameter; client-side limits of 5 requests per minute and a configurable daily cap; run records in `data/interim/tagging_runs/`.
- **Privacy:** review text is scrubbed of names, emails, phone numbers, handles and URLs before any request; dry run is the default and a real call needs `--run`, `--approve-gemini-data-processing` and `GEMINI_API_KEY`. Google's unpaid-tier terms say submitted content may be used to improve its products and reviewed by people (DECISIONS #22).
- **Protocol:** the prompt was tuned on the 40-review development split only; the configuration (model ID, prompt version) was then frozen (`data/interim/frozen_config.json`, enforced in code), and the 60-review test split was scored once (`eval_test.json` blocks a second run).
- **Gold set:** 100 Wispr reviews (85 Google Play, 7 App Store India, 8 App Store US), stratified by store, country, rating and language with seed 7 and a fixed 40/60 development/test split; one labeller, no second annotator. Labels were revised after the first development error analysis; two development labels were corrected in a documented audit (`docs/annotation_audit.md`). The evaluator accepts `;` or `,` theme separators and a TRUE/FALSE competitor flag, and excludes rows with no themes and no sentiment (counted, not scored).

## Development error analysis (prompt v1)
1. **Over-tagging:** the v1 prompt allowed 1-3 themes and the model usually returned 2-3 while the gold set mostly has one; many extra labels were `accuracy_general`.
2. **Praise false positives:** `praise_productivity` was added on top of a more specific theme (transcription quality, price, accessibility request).
3. **Convention:** the original label guide counted generic praise as `praise_productivity`; the revised gold labels and prompt v3 use `other` for generic praise and reserve `praise_productivity` for explicit time-saving, efficiency or habitual-use evidence (`docs/label_guide.md`).
4. **Inference beyond the text** (themes implied but not stated) and **sentiment disagreements** on mixed reviews.

## Prompt versions on the development split (n = 40, revised labels)
v1 is the baseline; v2 tightens theme assignment (one main theme, only what the text says); v3 additionally restricts `praise_productivity` to explicit productivity evidence. Scored from saved model outputs.

| prompt | n | micro-F1 (95% CI) | sentiment kappa (95% CI) |
|---|---|---|---|
| v1 | 40 | 0.645 (0.55-0.73) | 0.747 (0.55-0.91) |
| v2 | 40 | 0.643 (0.54-0.74) | 0.877 (0.73-1.00) |
| v3 | 40 | 0.752 (0.65-0.85) | 0.749 (0.57-0.91) |

Per-theme on dev (diagnostic; formal threshold is 5 gold examples). cells: precision / recall / F1.

| theme | support | v1 | v2 | v3 |
|---|---|---|---|---|
| accuracy_general | 11 | 0.61 / 1.00 / 0.76 | 0.91 / 0.91 / 0.91 | 0.91 / 0.91 / 0.91 |
| hinglish_code_switching | 1 | 0.50 / 1.00 / 0.67 | - / 0.00 / 0.00 | - / 0.00 / 0.00 |
| accent_or_noise | 0 | 0.00 / - / 0.00 | 0.00 / - / 0.00 | 0.00 / - / 0.00 |
| latency_speed | 1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| reliability_crash_bug | 4 | 0.33 / 0.50 / 0.40 | 0.20 / 0.25 / 0.22 | 0.20 / 0.25 / 0.22 |
| pricing_paywall | 4 | 0.80 / 1.00 / 0.89 | 0.60 / 0.75 / 0.67 | 0.80 / 1.00 / 0.89 |
| free_tier_limits | 3 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| privacy_trust | 1 | - / 0.00 / 0.00 | - / 0.00 / 0.00 | - / 0.00 / 0.00 |
| feature_request | 5 | 1.00 / 1.00 / 1.00 | 0.83 / 1.00 / 0.91 | 0.83 / 1.00 / 0.91 |
| praise_productivity | 7 | 0.35 / 1.00 / 0.52 | 0.39 / 1.00 / 0.56 | 0.67 / 0.86 / 0.75 |
| competitor_comparison | 1 | 0.50 / 1.00 / 0.67 | 0.33 / 1.00 / 0.50 | 0.33 / 1.00 / 0.50 |
| ui_ux | 6 | 0.62 / 0.83 / 0.71 | 0.67 / 0.67 / 0.67 | 0.67 / 0.67 / 0.67 |
| other | 8 | - / 0.00 / 0.00 | 1.00 / 0.12 / 0.22 | 0.86 / 0.75 / 0.80 |

Sentiment confusion (rows gold, columns predicted; neg/neu/pos):

- v1: neg: 11/0/1; neu: 3/3/2; pos: 0/0/20
- v2: neg: 12/0/0; neu: 2/5/1; pos: 0/0/20
- v3: neg: 11/0/1; neu: 4/3/1; pos: 0/0/20

**Reading.** v3 has the best micro-F1 (0.752) and best `praise_productivity` and `other` scores; v2 has the best sentiment kappa, but the sentiment instructions are identical across versions, so kappa differences are sampling noise. Confidence intervals overlap, temperature could not be fixed (run-to-run noise is unmeasured), most themes have fewer than five development examples (per-theme figures are diagnostics), and the revised labels followed the first error analysis, so development evidence for v3 is optimistic. v3 was frozen.

## Held-out test (n = 60, frozen v3, scored once)
| metric | development (n=40) | test (n=60) |
|---|---|---|
| micro-F1 (themes) | 0.752 (0.65-0.85) | **0.784** (0.72-0.85) |
| sentiment Cohen's kappa | 0.749 (0.57-0.91) | **0.830** (0.68-0.95) |

Bootstrap 95% intervals (1,000 resamples over reviews, seed 7). The run had 60 of 60 reviews tagged, no HTTP errors and no validation errors.

Themes with at least 5 gold test examples:

| theme | precision | recall | F1 | support |
|---|---|---|---|---|
| accuracy_general | 0.86 | 0.80 | 0.83 | 15 |
| reliability_crash_bug | 0.71 | 0.83 | 0.77 | 6 |
| pricing_paywall | 0.67 | 0.86 | 0.75 | 7 |
| feature_request | 0.86 | 0.86 | 0.86 | 7 |
| praise_productivity | 0.62 | 0.89 | 0.73 | 9 |
| ui_ux | 0.67 | 0.67 | 0.67 | 6 |
| other | 0.93 | 0.87 | 0.90 | 15 |

Themes with fewer than 5 test examples are **not evaluated** (counts only): hinglish_code_switching (support 3, false positives 1), accent_or_noise (support 0, false positives 1), latency_speed (support 1, false positives 0), onboarding_setup_permissions (support 2, false positives 0), free_tier_limits (support 0, false positives 1), privacy_trust (support 2, false positives 0), support_billing_cancellation (support 3, false positives 0), battery_performance (support 2, false positives 0), competitor_comparison (support 0, false positives 3), other_indian_language (support 4, false positives 0). Themes with zero test support that the model nonetheless predicted appear only as false positives.

Sentiment confusion on test (rows gold, columns predicted; neg/neu/pos): neg 18/1/2; neu 1/6/2; pos 0/0/30.

## Limitations
One labeller and no inter-annotator agreement; labels revised after the first development analysis; only 7 of 17 themes are evaluable on test and each interval is wide (support 6-15); the gold set is 85% Google Play and mostly English with 3 `hinglish_code_switching` and 4 `other_indian_language` test examples, so Hinglish performance is not established; the model is a free-tier endpoint whose behaviour can change; competitor reviews were not tagged or validated. The reproducibility consequence: review text and gold labels are not distributed, so these metrics can be re-derived only by someone with the same inputs (see `docs/reproducibility.md`).
