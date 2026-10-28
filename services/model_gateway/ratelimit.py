from __future__ import annotations

import threading
import time


class TokenBucket:
    """Small in-process token bucket; per-instance, not distributed."""

    def __init__(self, rate_per_second: float, burst: int) -> None:
        self.rate = rate_per_second
        self.burst = burst
        self._tokens = float(burst)
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        with self._lock:
            now = time.monotonic()
            self._tokens = min(self.burst, self._tokens + (now - self._updated) * self.rate)
            self._updated = now
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False
