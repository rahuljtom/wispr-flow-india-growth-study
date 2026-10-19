# Targets use the active Python by default; `make setup` creates .venv and installs dependencies.
PY ?= .venv/bin/python
BASE_PY ?= python3.12  # Python 3.11 or newer is required

.PHONY: setup test lint ledger-check layout-check check analyze charts value-ladder competitors dashboard deck reproduce

setup:
	$(BASE_PY) -m venv .venv
	.venv/bin/pip install -r requirements.txt

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check src tests

ledger-check:
	$(PY) -m src.common.check_ledger

layout-check:
	$(PY) -m src.deck.layout_check

# Tests, lint, number-to-ledger check and deck layout estimate.
check: test lint ledger-check layout-check

# Decomposition, Trends event study and experiment sizing (reads data/interim/trends_*.csv, writes data/processed and outputs/charts).
analyze:
	$(PY) -m src.analysis.run_p6

charts:
	$(PY) -m src.analysis.charts

value-ladder:
	$(PY) -m src.analysis.value_ladder

# Rebuilds the competitor matrix, ranking and sensitivity from data/interim/competitor_play_stats.csv.
competitors:
	$(PY) -m src.analysis.competitors

# Dashboard CSVs, the one-workbook export and the per-page Looker guides.
dashboard:
	$(PY) -m src.deck.dashboard_csv
	$(PY) -m src.deck.looker_docs

deck:
	$(PY) -m src.deck.build_deck

# Everything that can be regenerated from the files in this repository (no network, no API calls, no private data).
reproduce: analyze value-ladder competitors charts dashboard deck check
