from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    code = "ERROR"
    message_key = "errors.generic"
    details: list | dict | None = None

    if isinstance(exc, APIException):
        default_code = getattr(exc, "default_code", "generic")
        code = str(default_code).upper()
        message_key = getattr(exc, "message_key", f"errors.{default_code}")
        if isinstance(exc, InvalidToken) or default_code == "token_not_valid":
            message_key = "errors.auth.token_not_valid"

    payload = response.data
    if isinstance(payload, dict) and "detail" in payload:
        details = {"detail": payload["detail"]}
    elif isinstance(payload, (dict, list)):
        details = payload

    response.data = {
        "success": False,
        "error": {
            "code": code,
            "message_key": message_key,
            "details": details,
        },
    }
    return response
