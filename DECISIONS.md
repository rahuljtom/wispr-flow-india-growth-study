# Decision log

Decisions that shape the analysis, with status. "Superseded" rows are kept so references stay valid. Methodology rules are in `docs/methodology.md`; assumptions in `ASSUMPTIONS.md`.

| # | Decision | Status |
|---|---|---|
| 1 | Primary Google Trends query is "wispr flow"; misspellings are separate sensitivity checks | decided |
| 2 | Karnataka is the treated region and Maharashtra, Delhi, Tamil Nadu and Telangana the provisional controls, subject to pre-period diagnostics (in practice only Karnataka and Maharashtra were usable, so the comparison is not estimable) | provisional |
| 3 | Event date 2026-04-27 for the India launch and campaign. Economic Times (secondary, read via an archive.org capture; article dated 2026-04-28 IST) says the launch was "on Monday" and quotes a CEO post that day saying the autos were live; the weekday gives 2026-04-27. It is a launch-announcement date, not the first Hinglish release (earliest report 2026-02-23, R-089) or the Android launch (2026-02-23); a campaign start before 04-27 is not excluded | provisional (R-079, R-091) |
| 4 | Original competitor list: Gboard, Typeless, Aqua Voice, Superwhisper, Apple Dictation. Extended after a Google Play India search with Superflow, Bobble AI Keyboard, HinKhoj Hindi Voice Typing and SoundType AI; Soniox dropped (no verifiable India-relevant evidence). Scoring is by a written rubric (#30) | decided |
| 5 | Gold set of 100 Wispr reviews, 40 development / 60 test, stratified | decided |
| 6 | Tagging model | superseded by #21 (no Anthropic API key was available to the project) |
| 7 | Trends anchor handling: ratio to the anchor only where the anchor is non-zero and non-missing (rule 4) | decided |
| 8 | Scrub rules: names, emails, phones, handles and URLs removed before any model call (rule 8) | decided |
| 9 | Ledger statuses: reported, derived, assumption, estimated, unknown (`docs/ledger_schema.md`) | decided |
| 10 | Dashboard built manually in Looker Studio from generated tables (`docs/looker_studio_setup.md`); no report link is published in the repository | decided |
| 11 | Deck generated with python-pptx and matplotlib; every number must exist in the ledger | decided |
| 12 | Retired: project-management item, not part of the analysis | retired |
| 13 | Retired: local environment note | retired |
| 14 | Retired: local repository note | retired |
| 15 | App identifiers: Google Play `com.wispr.flowapp`, App Store `6497229487`; both listings resolve to "Wispr Flow: AI Voice-to-Text" by Wispr AI, Inc. (checked 2026-10-18) | verified |
| 16 | India-versus-US review comparison is "not estimable": Google Play reviews are not partitioned by country and the App Store feed returned non-overlapping windows. Review analysis uses overall Wispr themes plus a roman-Hindi/Devanagari subset labelled "language proxy, not geography" | decided |
| 17 | Trends anchor "voice typing" (non-zero mean in all five geos); the analysis uses the target as a share of its own pre-period mean | decided; revisit if anchor sparsity blocks the analysis |
| 18 | Retired: numbering gap | retired |
| 19 | Gold-set sampling: seed 7, 24 non-empty strata (store x country x rating x language), at least one review per stratum then proportional; composition 85 Play (country not available), 7 App Store India, 8 App Store US; India-specific coverage is thin | decided |
| 20 | Competitor review pulls and a competitor gold set were not done; competitor tags would be "unvalidated, directional" | decided |
| 21 | Tagging backend: Gemini free tier, Interactions API, model ID `gemini-3.5-flash-lite`, JSON-schema output, no temperature sent (not documented for this API), client limits 5 requests per minute and a configurable daily cap | decided |
| 22 | Gemini data processing: Google's unpaid-tier terms say submitted content may be used to improve its products and reviewed by people and advise against personal data; reviews are scrubbed of names, emails, phones, handles and URLs but are public store text. A real call needs an explicit approval flag | decided; applied to development, test and bulk runs |
| 23 | Protocol: tune the prompt on the development split only (at most v2, v3); freeze model and prompt; score the test split once (guards in code); gold labels are read-only inputs | decided |
| 24 | Prompt v2 was frozen first on the original labels (v3 had lower `praise_productivity` recall on them) | superseded by #25 |
| 25 | After the gold labels were revised, v3 had the best development micro-F1 and its generic-praise rule matched the revised labels, so the configuration was re-frozen to v3 (the superseded freeze is archived) | decided |
| 26 | Test split scored once with frozen v3: micro-F1 0.784, sentiment kappa 0.830 (`docs/tagging_eval.md`); `eval_test.json` blocks any rerun | done |
| 27 | Research update: India prices and payment methods taken from the India page; partner and student offers recorded as separate, non-universal offers; official docs show weekly free-tier caps on all platforms (Student plan unlimited); the launch-era Android free offer is not documented as current, so experiment E2 compares cap levels | done |
| 28 | Gold-label audit: gold_038 reduced to three themes and gold_094 moved to `competitor_comparison` (development split only); `praise_productivity` requires explicit time-saving, efficiency or habitual-use evidence; test labels unchanged | done (`docs/annotation_audit.md`) |
| 29 | Verification of remaining claims: Google says UPI works for Play subscriptions in India but Wispr-specific availability is unverified; net banking is not evidenced for Wispr and is discontinued on Play; the India page's third payment option is unnamed; partner-offer terms verified but current redeemability unknown; earliest Hinglish report 2026-02-23 (press), development date unknown | done |
| 30 | Competitor scoring audited: the rubric uses Google Play India listings; Play in-app price ranges are not compared with Flow's price because billing periods are unstated (price unknown for Superflow, Bobble, SoundType). Result: Gboard 13 of 15 (most dangerous substitute); Superflow 11 on four known criteria (11 to 14 possible; closest dedicated dictation rival); the Gboard-versus-Superflow order is not robust to dropping a criterion. Criterion `india_reach` replaced by `reach_global_play` (India's share of installs is not public) | done |
