"""Shared thread-safe token-bucket rate limiter (P3: extracted from the
OpenAlgo client so every provider uses the same policy).

Kite policy (roadmap): ~2.5 requests/second with jitter — i.e.
``TokenBucket(requests_per_minute=150, jitter_seconds=0.05)``.
"""

from __future__ import annotations

import random
import threading
import time


class TokenBucket:
    """Simple thread-safe token-bucket rate limiter (requests per minute).

    ``jitter_seconds`` adds a uniform [0, jitter] sleep after each acquire so
    bursty callers don't align into a metronome that trips upstream limits.
    """

    def __init__(self, requests_per_minute: int = 60, jitter_seconds: float = 0.0):
        self.capacity = max(1, int(requests_per_minute))
        self.tokens = float(self.capacity)
        self.refill_per_sec = self.capacity / 60.0
        self.jitter_seconds = max(0.0, float(jitter_seconds))
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.updated
                self.updated = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    break
                wait = (1.0 - self.tokens) / self.refill_per_sec
            time.sleep(wait)
        if self.jitter_seconds:
            time.sleep(random.uniform(0.0, self.jitter_seconds))
