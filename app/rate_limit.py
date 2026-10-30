

import math
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.errors import AppError


class RateLimiter:

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def __call__(self, request: Request) -> None:
        client_id = request.client.host if request.client else "unknown"
        now = time.monotonic()

        with self._lock:
            hits = self._hits[client_id]

            while hits and now - hits[0] >= self.window_seconds:
                hits.popleft()

            if len(hits) >= self.max_requests:
                retry_after = max(1, math.ceil(self.window_seconds - (now - hits[0])))
                raise AppError(
                    status_code=429,
                    code="rate_limited",
                    message="Too many requests. Please slow down and try again shortly.",
                    headers={"Retry-After": str(retry_after)},
                )

            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()



write_limiter = RateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_MAX", "5")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
)
