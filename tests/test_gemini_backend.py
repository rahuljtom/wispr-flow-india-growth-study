import json

import pytest

from src.tagging.backends import (
    DailyQuotaExhausted,
    GeminiClient,
    RateLimiter,
    ensure_approved,
    response_schema,
)
from src.tagging.tagger import TAXONOMY, build_payload

KEY = "SECRET-KEY-123"
GOOD = {"themes": ["ui_ux"], "sentiment": "neu", "mentions_competitor": None, "is_actionable": True}


def ok_response(tag=GOOD):
    # Shape follows the Interactions API reference (documentation-based fixture, not observed)
    return 200, {}, {"id": "i1", "status": "completed",
                     "steps": [{"type": "user_input"},
                               {"type": "model_output", "content": [{"type": "text", "text": json.dumps(tag)}]}],
                     "usage": {"total_input_tokens": 100, "total_output_tokens": 20,
                               "total_thought_tokens": 0}}


class Clock:
    def __init__(self):
        self.t = 1000.0
        self.slept = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


def make(post, tmp_path, clock=None, rpm=10, rpd=100, model="gemini-3.5-flash-lite"):
    clock = clock or Clock()
    lim = RateLimiter(rpm, rpd, tmp_path / "usage.json", now=clock.now, sleep=clock.sleep)
    return GeminiClient(KEY, model, lim, post=post, token_log=tmp_path / "tok.csv",
                        sleep=clock.sleep), clock


def test_request_shape_and_parse(tmp_path):
    seen = {}

    def post(url, headers, body, timeout):
        seen.update(url=url, headers=headers, body=body)
        return ok_response()

    c, _ = make(post, tmp_path)
    out = c(build_payload("k0", "nice app"))
    assert json.loads(out) == GOOD
    assert seen["url"].endswith("/v1beta/interactions")
    assert seen["headers"]["x-goog-api-key"] == KEY
    b = seen["body"]
    assert b["model"] == "gemini-3.5-flash-lite" and "system_instruction" in b
    assert b["response_format"]["mime_type"] == "application/json"
    assert b["response_format"]["schema"] == response_schema()
    assert "temperature" not in json.dumps(b)  # not documented for this API
    assert "nice app" in json.dumps(b) and KEY not in json.dumps(b)
    assert "100" in (tmp_path / "tok.csv").read_text()


def test_schema_uses_taxonomy():
    s = response_schema()
    assert s["properties"]["themes"]["items"]["enum"] == TAXONOMY
    assert set(s["required"]) == {"themes", "sentiment", "mentions_competitor", "is_actionable"}


def test_429_retry_after_honoured_then_succeeds(tmp_path):
    seq = iter([(429, {"Retry-After": "7"}, {"error": {"message": "quota"}}), ok_response()])
    c, clock = make(lambda *a, **k: next(seq), tmp_path)
    assert json.loads(c(build_payload("k", "x"))) == GOOD
    assert any(s >= 7 for s in clock.slept)


def test_429_gives_up_after_max_retries_without_leaking_key(tmp_path):
    calls = []

    def post(*a, **k):
        calls.append(1)
        return 429, {}, {"error": {"message": f"echo {KEY}"}}

    c, _ = make(post, tmp_path)
    with pytest.raises(RuntimeError) as e:
        c(build_payload("k", "x"))
    assert len(calls) == 4  # first try + 3 retries
    assert KEY not in str(e.value)


def test_missing_model_output_is_value_error(tmp_path):
    c, _ = make(lambda *a, **k: (200, {}, {"steps": [], "usage": {}}), tmp_path)
    with pytest.raises(ValueError):
        c(build_payload("k", "x"))


def test_rate_limiter_spacing_and_daily_cap(tmp_path):
    clock = Clock()
    lim = RateLimiter(6, 3, tmp_path / "u.json", now=clock.now, sleep=clock.sleep)  # 1 per 10 s
    for _ in range(3):
        lim.wait()
    assert sum(clock.slept) >= 20 - 1e-6
    with pytest.raises(DailyQuotaExhausted):
        lim.wait()
    # persisted across instances
    lim2 = RateLimiter(6, 3, tmp_path / "u.json", now=clock.now, sleep=clock.sleep)
    with pytest.raises(DailyQuotaExhausted):
        lim2.wait()


def test_approval_gate():
    with pytest.raises(PermissionError):
        ensure_approved(False, KEY)
    with pytest.raises(PermissionError):
        ensure_approved(True, "")
    ensure_approved(True, KEY)


def test_token_log_records_payload_prompt_version(tmp_path):
    c, _ = make(lambda *a, **k: ok_response(), tmp_path)
    c(build_payload("k0", "nice", version="v2"))
    assert ",v2," in (tmp_path / "tok.csv").read_text()
