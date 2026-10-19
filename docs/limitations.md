# Limitations and unresolved questions

**Evidence base**
- Public proxies only; there is no internal Wispr data. Revenue is in-app purchases only (Sensor Tower via TechCrunch, one secondary source); Wispr also bills web and desktop plans through Stripe, which that measure does not capture. The company says India is its second-largest base by users and paying subscribers, which does not fit 2% of in-app revenue unless much India revenue is billed outside the app stores (hypothesis).
- The price index uses an FX rate implied by a rounded figure in one article, annual-plan list prices only, and ignores realised prices, promotions, the free tier and billing route. The residual in the decomposition cannot be apportioned between price and other factors (range 0.223 to 1.224 across scenarios).

**Reviews**
- Google Play reviews are not partitioned by country and the App Store feed returned non-overlapping windows for India and US, so an India-versus-US comparison is **not estimable**. The roman-Hindi/Devanagari subset is a language proxy, not geography, and none of the tagged reviews fall in it.
- The tagged sample is interim: 321 of 600 selected reviews, all newest Google Play reviews (2026-07-30 to 2026-10-17); it is recency-biased and not all users.
- The tagger was validated on 100 reviews labelled by one person (no second annotator); labels were revised after the first development analysis; only 7 of 17 themes were evaluable on the 60-review test split. The model is a free-tier endpoint.

**Competitors and pricing**
- Scores rest on Google Play listings and developer claims. Install bands are global. Play in-app item ranges state no billing period and are not compared with Flow's price. Hinglish claims were not tested. Apple dictation and Google AI Edge Eloquent are unscored; Superwhisper has no Play listing found. The Gboard-versus-Superflow order is not robust to dropping a criterion.
- Payment methods and partner offers are advertised or documented, not tested; whether Wispr's Google Play subscription accepts UPI is unverified; the India page names only part of its payment options; offer redeemability today is unknown.

**Trends and campaign**
- Google Trends is relative and state-level; only two of five states had enough pre-period activity, so the Karnataka effect is not estimable. The campaign date (2026-04-27) is a reported launch date, not proof of the campaign start; the first technical Hinglish release is unknown.

**Experiments**
- Baselines and effect sizes are illustrative assumptions; guardrail limits need internal baselines; 1,650 installs a day is a whole-window average and probably understates current traffic.

**Dashboard**
- The Looker Studio report is built manually in a Google account; the repository contains data, a workbook and a build guide, not the report or any link.
