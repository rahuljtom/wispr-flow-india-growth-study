# Gold-label audit (2026-10-18)

Scope: all 100 labels in `data/private/gold_labels.csv`, checked against `docs/label_guide.md` and the convention built into frozen prompt v3 (a review is `praise_productivity` only with explicit time-saving, efficiency or habitual-use evidence; generic praise alone is `other`). Review IDs, text and the 40 dev / 60 test split are unchanged (verified cell-by-cell against the pre-audit backup `data/private/gold_labels.pre_audit_20261018.csv`: exactly two cells differ). Corrections were made only where the text and the written rules demonstrate an inconsistency, and only in the **dev** split. Test labels were not changed (guardrail: no changes to held-out labels after the test evaluation).

## Changes (dev split)
| gold_id | field | before | after | rationale |
|---|---|---|---|---|
| gold_038 | themes | reliability_crash_bug, accuracy_general, pricing_paywall, feature_request | reliability_crash_bug, accuracy_general, pricing_paywall | The guide caps themes at 3. Supported by the text: errors in dictated input (accuracy_general, said twice); a stated price of $18/mo (pricing_paywall); conflicts with work-profile clipboard restrictions and Android Auto (reliability_crash_bug). Rejected: `feature_request` (the offline wish is about what Android needs, not a request to Wispr; it is the weakest of the four); `support_billing_cancellation` (feedback "ignored" is a possible fifth theme, not added); dropping `reliability_crash_bug` instead is defensible but the compatibility defects are stated explicitly. Sentiment neg, competitor TRUE (Google voice dictation) and actionable TRUE unchanged. |
| gold_094 | themes | praise_productivity | competitor_comparison | Text: "Beats the hell out of Google." It compares against another product and gives no time-saving, efficiency or habitual-use evidence, so under the v3 convention it is not `praise_productivity`. `competitor_comparison` ("compares to another product") fits exactly. Rejected: `other` (a theme describes it). Sentiment pos, competitor TRUE, actionable FALSE unchanged. |

Effect on dev micro-F1 (no re-tagging): v1 0.640 to 0.645, v2 0.619 to 0.643, v3 0.727 to 0.752. Rules, not model outputs, determined the choices; the reviewer had seen earlier model outputs for these items, so the decision is documented here for confirmation or reversal from the backup.

## Reviewed and left unchanged (borderline, not demonstrable)
- gold_008 (dev) `praise_productivity, accuracy_general`: praises fluent, self-correcting speech input with no explicit time-saving or habitual-use statement; arguably accuracy only.
- gold_054 (dev) `praise_productivity, ui_ux`: habitual-use evidence is thin ("using it right now to write this review"); praise is mostly about fixed bugs.
- gold_030, gold_041 keep `praise_productivity` (two weeks of continuous use; "saves me a lot of time").
- gold_005, gold_038, gold_094 competitor TRUE are supported by the text (SwiftKey, Google). gold_055 (native iPhone dictation) is FALSE, consistent with gold_044 (test); native dictation is not treated as a named competitor.
- gold_040 and gold_099 (test) are 5-star with negative sentiment; the text contains a stated complaint, so they are consistent.

## Test split: report only (not changed)
- gold_016, gold_015, gold_073 (`praise_productivity`): evidence of productivity is implicit or truncated in the displayed text; gold_068 ("Very useful application in daily life") is `other` although "daily" could be read as habitual use. These are borderline readings of the convention, not clear errors. If the human wants them revised, the test result must be reported as "evaluated before label revision".

## Other label checks (all 100 rows)
Every theme is in the taxonomy; none empty or duplicated; `other` is never combined; after the audit no review has more than 3 themes; sentiment values are neg/neu/pos; TRUE/FALSE flags are consistent in form.
