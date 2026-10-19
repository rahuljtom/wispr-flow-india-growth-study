"""Numbers ledger (docs/ledger_schema.md)."""
import csv
from pathlib import Path

LEDGER = Path("data/ledger/numbers_ledger.csv")
ASSUMPTIONS = Path("ASSUMPTIONS.md")
STATUSES = {"reported", "derived", "assumption", "estimated", "unknown"}
COLS = ["claim_id", "used_in", "label", "value", "unit", "status", "source_url", "source_title",
        "source_date", "retrieved_on", "derivation", "n", "date_range", "caveat",
        "human_reviewed"]


def read_ledger(path=LEDGER):
    if not Path(path).exists():
        return []
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def add_claim(claim_id, used_in, label, value, unit, status, source_url="", source_title="",
              source_date="", retrieved_on="", derivation="", n="", date_range="", caveat="",
              human_reviewed="no", path=LEDGER, assumptions_path=ASSUMPTIONS):
    if status not in STATUSES:
        raise ValueError(f"bad status {status!r}")
    if status == "reported" and not source_url:
        raise ValueError("reported needs source_url")
    if status == "derived" and not derivation:
        raise ValueError("derived needs derivation with input claim_ids")
    if status == "estimated" and (n in ("", None) or not derivation):
        raise ValueError("estimated needs n and method/interval in derivation")
    if status == "unknown" and not caveat:
        raise ValueError("unknown needs a note on what is missing (caveat)")
    if status == "assumption":
        ap = Path(assumptions_path)
        if not ap.exists() or label not in ap.read_text():
            raise ValueError("assumption label must appear in ASSUMPTIONS.md")
    if any(r["claim_id"] == claim_id for r in read_ledger(path)):
        raise ValueError(f"duplicate claim_id {claim_id}")
    row = dict(zip(COLS, [claim_id, used_in, label, value, unit, status, source_url,
                          source_title, source_date, retrieved_on, derivation, n, date_range,
                          caveat, human_reviewed]))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        if new:
            w.writeheader()
        w.writerow(row)
