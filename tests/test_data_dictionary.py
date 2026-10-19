import csv
from pathlib import Path

DICT = Path("docs/data_dictionary.md").read_text(encoding="utf-8")


def test_every_dashboard_column_is_documented():
    for f in sorted(Path("outputs/dashboard").glob("dashboard_*.csv")):
        name = f.stem.replace("dashboard_", "")
        section = DICT.split(f"**{name}**")[1].split("\n\n")[0]
        for col in next(csv.reader(f.open(newline="", encoding="utf-8"))):
            assert f"`{col}`" in section, f"{name}.{col} missing from docs/data_dictionary.md"


def test_ledger_columns_documented():
    from src.common.ledger import COLS

    for c in COLS:
        assert c in DICT, c
