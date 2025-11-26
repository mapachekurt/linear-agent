"""Exponential backoff helper functions."""
from __future__ import annotations

import random
import time
from typing import Callable, Iterable

from .config import BackoffPolicy


def retry_with_backoff(
    func: Callable[[], object],
    exceptions: tuple[type[BaseException], ...],
    policy: BackoffPolicy,
    max_attempts: int = 5,
) -> object:
    """Retry ``func`` with exponential backoff on specified exceptions."""

    delay = policy.base_delay
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except exceptions:
            if attempt == max_attempts:
                raise
            jitter = random.uniform(-policy.jitter, policy.jitter) * delay
            time.sleep(min(policy.max_delay, delay + jitter))
            delay = min(policy.max_delay, delay * policy.multiplier)
    raise RuntimeError("Unreachable retry logic executed")


def backoff_delays(policy: BackoffPolicy, attempts: int) -> Iterable[float]:
    """Generate deterministic backoff delays for testing."""

    delay = policy.base_delay
    for _ in range(attempts):
        yield min(delay, policy.max_delay)
        delay = min(policy.max_delay, delay * policy.multiplier)
