"""Minimal JSON-over-HTTP client used by the agent to call tool endpoints.

Implemented on the standard library so the agent layer does not pull in an
extra HTTP client dependency. Services themselves are served with FastAPI.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class JsonHttpClient:
    def __init__(self, base_url: str, timeout: float = 10.0, headers: Optional[Dict[str, str]] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json", **(headers or {})}

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers=self.headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} from {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Connection error calling {path}: {exc.reason}") from exc

    def get(self, path: str) -> Dict[str, Any]:
        request = urllib.request.Request(f"{self.base_url}{path}", headers=self.headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} from {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Connection error calling {path}: {exc.reason}") from exc


def with_retry(fn, attempts: int = 3, base_delay: float = 0.2, max_delay: float = 2.0):
    """Exponential backoff with full jitter, matching the design's retry policy."""
    last_exc: Optional[Exception] = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - retry wrapper must catch all
            last_exc = exc
            if attempt == attempts - 1:
                break
            delay = min(max_delay, base_delay * (2**attempt))
            time.sleep(delay * (0.5 + (hash(str(exc)) % 1000) / 1000.0))
    assert last_exc is not None
    raise last_exc
