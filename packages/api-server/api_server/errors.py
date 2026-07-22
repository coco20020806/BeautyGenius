from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def new_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:12]}"


class ApiError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        request_id: str | None = None,
        details: Any = None,
    ):
        self.api_code = code
        self.api_message = message
        self.request_id = request_id or new_request_id()
        self.details = details
        super().__init__(status_code=status_code, detail=message)


def error_body(exc: ApiError) -> dict[str, Any]:
    return {
        "code": exc.api_code,
        "message": exc.api_message,
        "requestId": exc.request_id,
        "details": exc.details,
    }


async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=error_body(exc))
