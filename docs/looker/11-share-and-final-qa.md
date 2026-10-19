# 11 Sharing, access and final QA

Do this after all ten pages are built. Generated from `docs/looker_studio_setup.md`.

## Part 13. Sharing, access and the incognito test (Manual)

1. **Share** (top right) > **Manage access**. Under **General access** change **Restricted** to **Anyone with the link**, role **Viewer** (never Editor). Save. If a Google Workspace policy blocks public links, use another account or ask the workspace administrator.
2. **Resource > Manage added data sources**: every source shows **Owner's credentials**. The Google Sheet stays private.
3. **Share > Get report link**, copy. Do not use Embed.
4. **Incognito test:** open a private window (not signed in to Google), paste the link. All ten pages load, tabs navigate, no sign-in prompt, no red tiles; click a bar and press **Reset** to confirm interaction does not break anything.
5. **Privacy:** no review text, names, emails, phones, handles or review IDs appear (the data has none).
6. **Do not commit or publish** report links, Google Sheets, or data-source credentials in this repository.

---

## Part 14. Final QA checklist

**Data**
- [ ] Eleven sources named as in Part 1; owner's credentials; text columns are Text; the Sheet is private.
- [ ] `unknown` is visible in the competitor matrix and the pricing table; no unknown shows as 0; July is blank in `reviews_monthly`.

**Per page**
- [ ] 1: columns 14 and 2 from 0; cards 0.143 / 0.283 / 0.504; takeaway box.
- [ ] 2: 12 scenario rows 0.223 to 1.224; min/max cards; note on FX and window.
- [ ] 3: red INTERIM banner; ten bars two series from 0; cards 321 / 52 / 600; note.
- [ ] 4: 17 rows with intervals and counts; note on suppression.
- [ ] 5: banner; three lines Aug to Oct; July blank; table 3 / 80 / 145 / 93.
- [ ] 6: matrix of 10 candidates (Gboard 13 first; Superflow 11 with price `unknown`), the only 0 is Aqua Voice reach; 34 evidence rows; legend says Gboard vs Superflow order is not robust.
- [ ] 7: 8 bars from 0 (320 and 400 for India Pro); 14-row table with `unknown`, `free (...)` and unstated-period notes; FX note.
- [ ] 8: 7 offers, `UNVERIFIED`, payments note says advertised, not tested.
- [ ] 9: chart 11.2 / 25.5 / 9.5; numbers table; rules table with E3 proxy caveat.
- [ ] 10: 252-row grid, paginated.

**Design and wording**
- [ ] Same palette, type scale, margins and footer on all ten pages; no element overlaps; no truncated labels or headers.
- [ ] Cross-filtering (Apply filter) is off on every chart; **Reset** leaves every page unchanged.
- [ ] No causal wording; "directional", "scenario", "not estimable", "reported" used; limitations and the interim notice present.

**Privacy and access**
- [ ] No review text or identifiers; sharing is Anyone with the link, Viewer; the incognito test passed on all ten pages; the link in the form is the tested link.

---

## Part 15. Troubleshooting

| Symptom | Fix |
|---|---|
| One category (for example `free_tier_limits`) shows everywhere | Cross-filter from clicking a bar. **Reset**, then untick **Apply filter** on each chart (2.5). |
| Numbers doubled or too large | Aggregation is Sum. Click the metric pill and choose **Max**. |
| A field you need is missing in the pill list | The chart uses the wrong data source; change **Setup > Data source**. Fields come only from that source. |
| Percent shows `0.215` | You are using an old field. Use `*_pct` fields (already in percent units). |
| Month labels look like `month=2026-10` or are in reverse order | Old data. Re-import the new workbook (Part 1) and use `month_label`; sort ascending. |
| `unknown` became blank | Re-import from the original xlsx; keep the five criterion columns, `score`, `usd_list_price`, `inr_per_month` as Text. |
| Table headers truncated | Edit **Display name** of the field, widen the column, enable **Wrap text**, reduce font to 10. |
| Chart empty | Check the source and that the fields exist; open the source in **Resource** and **Refresh fields**. |
| "Data set configuration error" in View | Credentials are not Owner's, or the Sheet was moved or deleted. Reconnect. |
| Text cut off in a text box | Enlarge the box or reduce the font; boxes do not auto-grow. |
| Data changed in the Sheet but not in the report | In View mode use the refresh icon; or **Resource > Manage added data sources > Edit > Refresh fields**. |
| Line chart shows a zero for July | Style: **Missing data** must be **line breaks**. July is meant to be blank. |

---

## Part 16. Unresolved items and limits of this manual

- **Interface variation.** Menu names, especially **Chart interactions**, **Position/Size**, **Conditional formatting on text** and **Missing data**, can differ by Looker Studio version. Each place has a fallback. The guide was written from Google's documentation and could not be run against the live product, so the manual is a best description, not a recording.
- **Interim sample.** 321 of 600 reviews are tagged; the tagging job is paused by an apparent daily quota. When it finishes: regenerate (`python -m src.analysis.run_a1`, then `python -m src.deck.dashboard_csv`), re-import the workbook into the same Sheet, **Refresh fields**, and the banner changes automatically.
- **Unverified evidence on pages 6 to 8.** Wispr-specific UPI on Google Play, the unnamed third payment option, offer redeemability today, the first Hinglish release date.
- **Implied FX.** 94.1 INR per USD comes from TechCrunch's rounded conversion; there is no independent FX rate.
- **Competitor evidence.** Scores come from Google Play listings (install bands are global, not India), developer claims and vendor pages. Apple dictation and Google AI Edge Eloquent are unscored; Superwhisper has no Play listing found. Hinglish and price claims are advertised, not tested.
