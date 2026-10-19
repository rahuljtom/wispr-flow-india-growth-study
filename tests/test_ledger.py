import pytest

from src.common.ledger import add_claim

B = {"claim_id": "X-1", "used_in": "s2", "label": "thing", "value": 1, "unit": "x"}


def test_reported_needs_url(tmp_path):
    with pytest.raises(ValueError):
        add_claim(**B, status="reported", path=tmp_path / "l.csv")
    add_claim(**B, status="reported", source_url="http://a", retrieved_on="2026-10-18",
              path=tmp_path / "l.csv")


def test_derived_needs_inputs(tmp_path):
    with pytest.raises(ValueError):
        add_claim(**B, status="derived", path=tmp_path / "l.csv")
    add_claim(**B, status="derived", derivation="a/b from R-1,R-2", path=tmp_path / "l.csv")


def test_estimated_needs_n_method_interval(tmp_path):
    with pytest.raises(ValueError):
        add_claim(**B, status="estimated", path=tmp_path / "l.csv")
    add_claim(**B, status="estimated", n=100, derivation="method: wilson; CI 0.1-0.2",
              path=tmp_path / "l.csv")


def test_unknown_needs_note(tmp_path):
    with pytest.raises(ValueError):
        add_claim(**B, status="unknown", path=tmp_path / "l.csv")
    add_claim(**B, status="unknown", caveat="missing: source", path=tmp_path / "l.csv")


def test_assumption_must_be_in_assumptions_md(tmp_path):
    a = tmp_path / "A.md"
    a.write_text("| thing | 1 |")
    add_claim(**B, status="assumption", path=tmp_path / "l.csv", assumptions_path=a)
    with pytest.raises(ValueError):
        add_claim(**{**B, "label": "other"}, status="assumption", path=tmp_path / "l.csv",
                  assumptions_path=a)


def test_bad_status_and_duplicate_id(tmp_path):
    with pytest.raises(ValueError):
        add_claim(**B, status="confirmed", path=tmp_path / "l.csv")
    add_claim(**B, status="unknown", caveat="m", path=tmp_path / "l.csv")
    with pytest.raises(ValueError):
        add_claim(**B, status="unknown", caveat="m", path=tmp_path / "l.csv")
