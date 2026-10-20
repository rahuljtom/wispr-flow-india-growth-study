-- Share of reviews carrying each theme, per segment, with Wilson 95% intervals.
-- A review can carry up to three themes, so shares do not sum to 1. Segments with fewer than $min_n
-- reviews are suppressed: share and interval are NULL (blank), never 0. mean_rating is NULL when the
-- segment is suppressed or no review carries the theme.
-- Parameters: $min_n, $z. Views: segment_members(segment, seg_order, sub_order, review_key),
-- reviews(review_key, rating, ...), review_themes(review_key, theme), taxonomy(theme, ord).
WITH seg AS (
    SELECT sm.segment, sm.seg_order, sm.sub_order, count(DISTINCT sm.review_key) AS n_segment
    FROM segment_members sm GROUP BY ALL
),
cell AS (
    SELECT s.segment, s.seg_order, s.sub_order, s.n_segment, t.theme, t.ord,
           count(DISTINCT rt.review_key) AS n_with_theme,
           avg(r.rating) FILTER (WHERE rt.review_key IS NOT NULL) AS mean_rating_raw
    FROM seg s
    CROSS JOIN taxonomy t
    LEFT JOIN segment_members sm ON sm.segment = s.segment AND sm.sub_order = s.sub_order
    LEFT JOIN review_themes rt ON rt.review_key = sm.review_key AND rt.theme = t.theme
    LEFT JOIN (SELECT DISTINCT review_key, rating FROM reviews) r ON r.review_key = rt.review_key
    GROUP BY ALL
),
stats AS (
    SELECT *, n_segment < $min_n AS suppressed,
           n_with_theme::DOUBLE / n_segment AS p,
           1 + $z * $z / n_segment AS d
    FROM cell
),
wilson AS (
    SELECT *, (p + $z * $z / (2 * n_segment)) / d AS c,
           $z * sqrt(p * (1 - p) / n_segment + $z * $z / (4 * n_segment * n_segment)) / d AS h
    FROM stats
)
SELECT segment, theme, n_segment, n_with_theme,
       CASE WHEN suppressed THEN NULL ELSE p END AS share,
       CASE WHEN suppressed THEN NULL ELSE greatest(0.0, c - h) END AS ci_lo,
       CASE WHEN suppressed THEN NULL ELSE least(1.0, c + h) END AS ci_hi,
       CASE WHEN suppressed OR n_with_theme = 0 THEN NULL ELSE mean_rating_raw END AS mean_rating,
       suppressed
FROM wilson
ORDER BY seg_order, sub_order, ord;
