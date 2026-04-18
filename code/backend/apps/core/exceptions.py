import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("quantyield")


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler to produce a consistent JSON envelope:
        {"error": "<type>", "detail": "<message>", "status_code": N}
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_type = type(exc).__name__
        detail = response.data

        # Flatten single-key dicts {"detail": "..."} to just the string
        if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
            detail = str(detail["detail"])

        response.data = {
            "error": error_type,
            "detail": detail,
            "status_code": response.status_code,
        }
        logger.warning("API error %s: %s", error_type, detail)
    else:
        # Unhandled exception → 500
        logger.exception("Unhandled exception in API: %s", exc)
        response = Response(
            {
                "error": type(exc).__name__,
                "detail": "An unexpected server error occurred.",
                "status_code": 500,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
