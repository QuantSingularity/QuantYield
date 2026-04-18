import logging
import time

logger = logging.getLogger("quantyield")


class RequestTimingMiddleware:
    """Log each request with elapsed time."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t0 = time.monotonic()
        response = self.get_response(request)
        elapsed_ms = (time.monotonic() - t0) * 1000
        logger.debug(
            "%s %s → %s  (%.1f ms)",
            request.method,
            request.path,
            response.status_code,
            elapsed_ms,
        )
        response["X-Response-Time-Ms"] = f"{elapsed_ms:.1f}"
        return response
