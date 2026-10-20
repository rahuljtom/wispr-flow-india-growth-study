-- Effective INR per month per product and plan, at the FX implied by the TechCrunch conversion.
-- Parameters: $fx (INR per USD), $india_annual_inr, $india_monthly_inr (India page prices, used as stated).
-- View: pricing = data/processed/competitor_pricing.csv. A non-numeric USD price ("unknown",
-- "not applicable") gives a NULL INR price, never 0. round_even matches Python and numpy rounding
-- (ties go to the even neighbour); plain round() would differ on exact .5 values.
SELECT p.*,
       round_even(CASE
                 WHEN p.product = 'Wispr Flow' AND p.plan = 'India Pro' AND p.billing = 'annual'
                     THEN $india_annual_inr
                 WHEN p.product = 'Wispr Flow' AND p.plan = 'India Pro' AND p.billing = 'monthly'
                     THEN $india_monthly_inr
                 ELSE TRY_CAST(p.price_usd_per_month AS DOUBLE) * $fx
             END, 0) AS price_inr_per_month,
       round_even($fx, 1) AS fx_inr_per_usd,
       'implied by TechCrunch 2026-05-09 (Rs 320 = about $3.4); not an independent FX source' AS fx_basis
FROM pricing p;
