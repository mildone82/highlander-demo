from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class CircuitBreaker:
    """Sliding-window failure counter with a cooldown open state."""

    failure_threshold: int = 3
    recovery_timeout_s: float = 30.0

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._failures = 0
        self._opened_at: Optional[float] = None

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._opened_at = time.monotonic()

    def allow(self) -> bool:
        with self._lock:
            if self._opened_at is None:
                return True
            if time.monotonic() - self._opened_at >= self.recovery_timeout_s:
                # Half-open: permit one probe.
                self._opened_at = None
                self._failures = 0
                return True
            return False
