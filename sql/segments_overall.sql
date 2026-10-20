-- Review segments for the overall theme table: which reviews belong to which segment.
-- View: reviews(review_key, rating, store, country, lang_proxy, month).
-- seg_order and sub_order only fix the row order (all, low-rated, by store, by language proxy,
-- App Store by country). App Store countries come from two partial pages and are not comparable.
SELECT 'all tagged sample' AS segment, 0 AS seg_order, '' AS sub_order, review_key FROM reviews
UNION ALL
SELECT 'rating<=2 (low-rated)', 1, '', review_key FROM reviews WHERE rating <= 2
UNION ALL
SELECT 'store=' || store, 2, store, review_key FROM reviews
UNION ALL
SELECT lang_proxy, 3, lang_proxy, review_key FROM reviews
UNION ALL
SELECT 'appstore ' || country || ' (not comparable windows)', 4, country, review_key
FROM reviews WHERE store = 'appstore'
