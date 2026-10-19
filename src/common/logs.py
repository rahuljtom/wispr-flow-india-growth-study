"""Pull and failure logs (rule 10)."""
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

LOG_DIR = Path("data/logs")
MAX_RETRIES = 3
PULL_COLS = ["pull_id", "source", "endpoint", "params_json", "pulled_at_utc", "rows", "sha256",
             "status"]
FAIL_COLS = ["pull_id", "error", "retry_n", "resolved"]


def _append(path, cols, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        if new:
            w.writeheader()
        w.writerow(row)


def append_pull(pull_id, source, endpoint, params, file_path, rows, status="ok",
                log_dir=LOG_DIR):
    data = Path(file_path).read_bytes()  # raises FileNotFoundError if missing
    _append(Path(log_dir) / "pull_log.csv", PULL_COLS, {
        "pull_id": pull_id, "source": source, "endpoint": endpoint,
        "params_json": json.dumps(params, sort_keys=True),
        "pulled_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "rows": rows, "sha256": hashlib.sha256(data).hexdigest(), "status": status})


def append_failure(pull_id, error, retry_n, resolved, log_dir=LOG_DIR):
    if retry_n > MAX_RETRIES:
        raise ValueError(f"retry_n {retry_n} exceeds max {MAX_RETRIES}")
    _append(Path(log_dir) / "failure_log.csv", FAIL_COLS,
            {"pull_id": pull_id, "error": error, "retry_n": retry_n, "resolved": resolved})
