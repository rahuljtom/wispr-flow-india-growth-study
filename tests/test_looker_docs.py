import re
from pathlib import Path

import src.deck.looker_docs as ld


def test_page_guides_exist_in_sync_and_cover_every_source(tmp_path, monkeypatch):
    monkeypatch.setattr(ld, "OUT", tmp_path)
    ld.main()
    for f in tmp_path.glob("*.md"):  # generated output equals the committed guides (no hand edits, no drift)
        assert f.read_text(encoding="utf-8") == (Path("docs/looker") / f.name).read_text(encoding="utf-8"), f.name
    assert len(list(tmp_path.glob("page-*.md"))) == 10
    used = set()
    for slug, _title, _part, sources, _status in ld.PAGES:
        text = (tmp_path / f"{slug}.md").read_text(encoding="utf-8")
        assert "STOP AND VERIFY" in text and "Apply filter" in text and "Part " not in re.sub(r"\(.*?\)", "", text.split("## Build steps")[1].split("## Page checklist")[0]).replace("Part of", "")
        for s in sources:
            n_rows, n_cols = ld.counts(s)
            assert f"| `{s}` | {n_rows} | {n_cols} |" in text
            used.add(s)
    assert used == {"summary", "decomposition", "reviews_themes", "reviews_monthly", "competitors_matrix",
                    "competitors_evidence", "pricing_chart", "pricing", "offers", "experiments_headline", "experiments_grid"}
