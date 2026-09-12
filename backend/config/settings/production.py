import os

from .base import *  # noqa: F403

DEBUG = False
DJANGO_ADMIN_ENABLED = False

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _render_host:
    ALLOWED_HOSTS.append(_render_host)

# Northflank public host: p01--service--xxxx.code.run
if "*" not in ALLOWED_HOSTS and ".code.run" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".code.run")

_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if _csrf_origins.strip():
    CSRF_TRUSTED_ORIGINS = [
        origin.strip() for origin in _csrf_origins.split(",") if origin.strip()
    ]
else:
    CSRF_TRUSTED_ORIGINS = [
        origin if origin.startswith("http") else f"https://{origin}"
        for origin in CORS_ALLOWED_ORIGINS
    ]
