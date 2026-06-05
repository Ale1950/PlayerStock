"""Machine-readable error helpers (i18n-friendly).

All errors raised by the API return a body shaped as:
    {"error_code": "user.not_found", "message_it": "Utente non trovato"}

The client maps `error_code` to a localized string via i18next.
`message_it` is the Italian fallback (and current UI language in MVP).
"""
from __future__ import annotations

from fastapi import HTTPException, status


class APIError(HTTPException):
    def __init__(self, *, http_status: int, error_code: str, message_it: str, extra: dict | None = None) -> None:
        body = {"error_code": error_code, "message_it": message_it}
        if extra:
            body["extra"] = extra
        super().__init__(status_code=http_status, detail=body)


# Pre-defined errors
def err_unauthorized(code: str = "auth.unauthorized", msg: str = "Non autorizzato") -> APIError:
    return APIError(http_status=status.HTTP_401_UNAUTHORIZED, error_code=code, message_it=msg)


def err_forbidden(code: str = "auth.forbidden", msg: str = "Accesso negato") -> APIError:
    return APIError(http_status=status.HTTP_403_FORBIDDEN, error_code=code, message_it=msg)


def err_not_found(code: str = "resource.not_found", msg: str = "Risorsa non trovata") -> APIError:
    return APIError(http_status=status.HTTP_404_NOT_FOUND, error_code=code, message_it=msg)


def err_bad_request(code: str, msg: str, extra: dict | None = None) -> APIError:
    return APIError(http_status=status.HTTP_400_BAD_REQUEST, error_code=code, message_it=msg, extra=extra)


def err_conflict(code: str, msg: str) -> APIError:
    return APIError(http_status=status.HTTP_409_CONFLICT, error_code=code, message_it=msg)
