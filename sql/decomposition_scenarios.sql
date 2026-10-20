-- Scenario decomposition of the India install-vs-revenue gap (arithmetic identity, not causal).
-- revenue-per-install index = price index x residual index.
-- Parameters: $install_share, $rev_share, $india_price, $global_price, $window_days, $price_start_day.
-- View: missed(missed_share) = assumed share of India revenue missing from the source.
-- Price applies to f of the window, f in {0.5, share of window after the price start, 1.0}.
WITH windows AS (
    SELECT DISTINCT f FROM (
        VALUES (0.5),
               (($window_days - $price_start_day)::DOUBLE / $window_days),
               (1.0)
    ) AS t(f)
),
grid AS (
    SELECT m.missed_share, w.f AS price_window_share,
           -- India revenue share if a fraction is missing (global revenue assumed fully observed)
           (($rev_share / (1 - m.missed_share))
            / (($rev_share / (1 - m.missed_share)) + (1 - $rev_share))) / $install_share
               AS rev_per_install_index,
           (1 - w.f) + w.f * $india_price / $global_price AS price_index
    FROM missed m CROSS JOIN windows w
)
SELECT missed_share, price_window_share, rev_per_install_index, price_index,
       rev_per_install_index / price_index AS residual_index
FROM grid
ORDER BY missed_share, price_window_share;
