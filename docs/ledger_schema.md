# Ledger schema

| Column | Meaning |
|---|---|
| claim_id | Stable ID, e.g. R-001 |
| used_in | Slide number or chart file |
| label | Plain-language description |
| value, unit | The number and its unit |
| status | reported / derived / assumption / estimated / unknown |
| source_url, source_title, source_date, retrieved_on | Required for reported; blank allowed for assumption/unknown |
| derivation | For derived/estimated: formula and the input claim_ids |
| n, date_range | Sample size and period where relevant |
| caveat | One line, shown in footnote if material |
| human_reviewed | yes/no: whether a person has checked the row |

Status rules: reported needs a URL; derived needs input claim_ids; estimated needs n, method and an interval or "not estimable"; assumption must also appear in ASSUMPTIONS.md; unknown needs a "what is missing" note.
