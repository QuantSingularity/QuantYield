import sys

import numpy as np
import pandas as pd
import scipy
from django.conf import settings
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle


@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
def root_view(request):
    """API root / info."""
    return Response(
        {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "operational",
            "description": "Institutional-grade fixed income analytics platform",
            "docs": "/docs/",
            "redoc": "/redoc/",
            "admin": "/admin/",
            "endpoints": {
                "bonds": "/api/v1/bonds/",
                "portfolios": "/api/v1/portfolios/",
                "curves": "/api/v1/curves/",
                "analytics": "/api/v1/analytics/",
            },
        }
    )


@api_view(["GET"])
@throttle_classes([AnonRateThrottle])
def health_view(request):
    """Detailed health check."""
    torch_version = None
    try:
        import torch

        torch_version = torch.__version__
    except ImportError:
        pass

    from django.db import connection

    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    return Response(
        {
            "status": "ok",
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "python": sys.version,
            "django": __import__("django").__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pandas": pd.__version__,
            "torch": torch_version or "not installed (AR(1) fallback active)",
            "database": "ok" if db_ok else "error",
            "fred_api_key": bool(settings.FRED_API_KEY),
            "forecaster": "lstm" if torch_version else "arima",
        }
    )
