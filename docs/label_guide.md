# Gold-set labelling guide (taxonomy v1)

File to label: `data/private/gold_blind.csv` (100 Wispr reviews, `gold_id` + `text`). Fill four columns per row. Do not look at any model output while labelling.

- **themes**: 1 to 3 values from the list below, separated by `;` (e.g. `latency_speed;praise_productivity`). Use `other` only if nothing fits.
- **sentiment**: `neg`, `neu` or `pos` (overall tone toward the app).
- **mentions_competitor**: name of another product the review mentions (e.g. Gboard, Otter), else leave blank.
- **is_actionable**: `true` if the review gives specific, fixable product feedback; otherwise `false`.

| theme | use when the review is about |
|---|---|
| accuracy_general | transcription correctness or mistakes in general |
| hinglish_code_switching | mixing Hindi and English, Hinglish, Roman-script Hindi output |
| accent_or_noise | accents, background noise, speaking style |
| latency_speed | delay, slow response, lag |
| reliability_crash_bug | crashes, bugs, stops working, dropouts |
| onboarding_setup_permissions | install, sign-in, setup steps, accessibility/overlay/mic permissions |
| pricing_paywall | price, paywall, value for money, regional pricing |
| free_tier_limits | weekly word limits, free plan caps |
| privacy_trust | data, recordings, security, trust |
| support_billing_cancellation | support responses, charges, refunds, cancelling |
| battery_performance | battery drain, heat, memory, device slowdown |
| feature_request | asks for a feature or option |
| praise_productivity | positive review that states a time-saving, efficiency or productivity benefit, or habitual use as a result (for example "saves me time"). Generic praise without such evidence ("amazing app", "good app") is `other`. Praise specifically about transcription quality is `accuracy_general` |
| competitor_comparison | compares to another product |
| other_indian_language | Indian languages other than Hindi/Hinglish |
| ui_ux | layout, bubble/overlay behaviour, design, usability |
| other | none of the above |

Save the labelled file as `data/private/gold_labels.csv` (same columns) and tell me "labels complete".
