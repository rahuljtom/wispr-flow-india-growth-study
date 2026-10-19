"""Gemini backend for review tagging (Interactions API, per ai.google.dev docs read 2026-10-18).

Safety properties: the API key is read from the environment only and is sent only in the
x-goog-api-key header; error messages never include response bodies or the key. A request is
made only through GeminiClient, which the CLI builds only after explicit approval.
"""
import csv
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from src.tagging.tagger import MODEL, PROMPT_VERSION, SENTIMENTS, TAXONOMY

URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_MODEL = MODEL
MAX_RETRIES = 3
MAX_OUTPUT_TOKENS = 1024
PACIFIC = ZoneInfo("America/Los_Angeles")  # free-tier RPD resets at midnight Pacific


class DailyQuotaExhausted(RuntimeError):
    pass


def ensure_approved(approved, key):
    if not approved:
        raise PermissionError("Gemini data processing not approved (--approve-gemini-data-processing)")
    if not key:
        raise PermissionError("GEMINI_API_KEY is not set")


def response_schema():
    return {
        "type": "object",
        "properties": {
            "themes": {"type": "array", "minItems": 1, "maxItems": 3,
                       "items": {"type": "string", "enum": TAXONOMY}},
            "sentiment": {"type": "string", "enum": SENTIMENTS},
            "mentions_competitor": {"type": ["string", "null"]},
            "is_actionable": {"type": "boolean"},
        },
        "required": ["themes", "sentiment", "mentions_competitor", "is_actionable"],
    }


class RateLimiter:
    """Spaces requests at <= rpm and stops at rpd per Pacific day (persisted across runs)."""

    def __init__(self, rpm, rpd, state_path, now=time.time, sleep=time.sleep):
        self.interval = 60.0 / rpm
        self.rpd = rpd
        self.path = Path(state_path)
        self.now, self.sleep = now, sleep
        self.last = None

    def _day(self):
        return datetime.fromtimestamp(self.now(), PACIFIC).strftime("%Y-%m-%d")

    def _count(self):
        if self.path.exists():
            s = json.loads(self.path.read_text())
            if s.get("date") == self._day():
                return s["count"]
        return 0

    def wait(self):
        n = self._count()
        if n >= self.rpd:
            raise DailyQuotaExhausted(f"daily request budget {self.rpd} reached; resume after "
                                      "midnight Pacific")
        if self.last is not None:
            gap = self.last + self.interval - self.now()
            if gap > 0:
                self.sleep(gap)
        self.last = self.now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"date": self._day(), "count": n + 1}))


def _http_post(url, headers, body, timeout):
    try:
        r = requests.post(url, headers=headers, json=body, timeout=timeout)
    except requests.RequestException as e:
        raise RuntimeError(f"network error: {type(e).__name__}") from None
    try:
        data = r.json()
    except ValueError:
        data = {}
    return r.status_code, dict(r.headers), data


class GeminiClient:
    def __init__(self, key, model, limiter, post=_http_post, sleep=time.sleep,
                 token_log=Path("data/logs/token_log.csv"), timeout=60):
        self._key, self.model, self.limiter = key, model, limiter
        self.post, self.sleep, self.token_log, self.timeout = post, sleep, Path(token_log), timeout
        self.prompt_version = PROMPT_VERSION
        self.stats = {"requests": 0, "http_429": 0, "http_other_errors": 0}

    def config(self, prompt_version=PROMPT_VERSION):
        return {"provider": "gemini", "endpoint": URL, "model_id": self.model,
                "prompt_version": prompt_version, "rpm": round(60.0 / self.limiter.interval, 3),
                "rpd": self.limiter.rpd, "max_output_tokens": MAX_OUTPUT_TOKENS,
                "temperature": "not set (not documented for the Interactions API)",
                "response_format": "application/json with JSON schema"}

    def _body(self, payload):
        return {"model": self.model, "input": payload["user"],
                "system_instruction": payload["system"],
                "generation_config": {"max_output_tokens": MAX_OUTPUT_TOKENS},
                "response_format": {"type": "text", "mime_type": "application/json",
                                    "schema": response_schema()}}

    def __call__(self, payload):
        headers = {"x-goog-api-key": self._key, "Content-Type": "application/json"}
        body = self._body(payload)
        for attempt in range(MAX_RETRIES + 1):
            self.limiter.wait()
            self.stats["requests"] += 1
            status, resp_headers, data = self.post(URL, headers, body, self.timeout)
            if status == 200:
                self.prompt_version = payload.get("prompt_version", PROMPT_VERSION)
                self._log_tokens(data.get("usage", {}))
                return self._text(data)
            retryable = status == 429 or status >= 500
            self.stats["http_429" if status == 429 else "http_other_errors"] += 1
            if not retryable:
                raise RuntimeError(f"Gemini HTTP {status}")
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Gemini HTTP {status} after {MAX_RETRIES} retries")
            retry_after = {k.lower(): v for k, v in resp_headers.items()}.get("retry-after")
            try:
                wait = float(retry_after)
            except (TypeError, ValueError):
                wait = 0.0
            self.sleep(max(wait, self.limiter.interval * 2 ** (attempt + 1)))

    @staticmethod
    def _text(data):
        for step in data.get("steps", []):
            if step.get("type") == "model_output":
                text = "".join(c.get("text", "") for c in step.get("content", []))
                if text:
                    return text
        raise ValueError("no model_output text in response")

    def _log_tokens(self, usage):
        self.token_log.parent.mkdir(parents=True, exist_ok=True)
        new = not self.token_log.exists()
        with open(self.token_log, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["utc", "model", "prompt_version", "input_tokens", "output_tokens",
                            "thought_tokens"])
            w.writerow([datetime.now(UTC).isoformat(timespec="seconds"), self.model,
                        self.prompt_version, usage.get("total_input_tokens", ""),
                        usage.get("total_output_tokens", ""), usage.get("total_thought_tokens", "")])
