-- Review segments by calendar month of the review date (UTC month computed upstream).
-- View: reviews(review_key, rating, store, country, lang_proxy, month).
SELECT 'month=' || month AS segment, 0 AS seg_order, month AS sub_order, review_key FROM reviews
