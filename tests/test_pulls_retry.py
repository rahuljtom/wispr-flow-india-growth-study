import pytest

from src.pulls.reviews import with_retries


def test_succeeds_after_failures_and_logs(tmp_path):
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("boom")
        return "ok"

    assert with_retries("p1", fn, log_dir=tmp_path, sleep=lambda s: None) == "ok"
    assert (tmp_path / "failure_log.csv").read_text().count("\n") == 3  # header + 2 failures


def test_gives_up_after_three_retries(tmp_path):
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        with_retries("p2", fn, log_dir=tmp_path, sleep=lambda s: None)
    assert calls["n"] == 4  # first try + 3 retries
