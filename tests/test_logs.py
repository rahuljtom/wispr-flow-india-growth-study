import csv
import hashlib

import pytest

from src.common.logs import append_failure, append_pull


def rows(p):
    return list(csv.DictReader(open(p)))


def test_pull_hash_correct(tmp_path):
    f = tmp_path / "x.json"
    f.write_bytes(b"hello")
    append_pull("pid1", "src", "ep", {"a": 1}, f, rows=3, log_dir=tmp_path)
    r = rows(tmp_path / "pull_log.csv")[0]
    assert r["sha256"] == hashlib.sha256(b"hello").hexdigest()
    assert r["pull_id"] == "pid1" and r["rows"] == "3" and r["status"] == "ok"


def test_pull_missing_file_refused(tmp_path):
    with pytest.raises(FileNotFoundError):
        append_pull("p", "s", "e", {}, tmp_path / "nope", rows=0, log_dir=tmp_path)
    assert not (tmp_path / "pull_log.csv").exists()


def test_retry_never_exceeds_3(tmp_path):
    for n in (1, 2, 3):
        append_failure("p", "err", n, False, log_dir=tmp_path)
    with pytest.raises(ValueError):
        append_failure("p", "err", 4, False, log_dir=tmp_path)
    assert len(rows(tmp_path / "failure_log.csv")) == 3
