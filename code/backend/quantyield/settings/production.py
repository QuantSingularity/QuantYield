from .base import *  # noqa

DEBUG = False

# In production, set ALLOWED_HOSTS via environment
# ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Stricter security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Use Redis cache in production
# Set CACHE_URL=redis://localhost:6379/1 in .env

# Production permissions: require authentication for write operations
REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = [  # noqa: F405
    "rest_framework.permissions.IsAuthenticatedOrReadOnly",
]
