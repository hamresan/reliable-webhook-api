from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, max_payload_bytes: int) -> None:
        super().__init__(app)
        self._max_payload_bytes = max_payload_bytes

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    if int(content_length) > self._max_payload_bytes:
                        return JSONResponse(
                            status_code=413,
                            content={"detail": "Request payload is too large."},
                        )
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid Content-Length header."},
                    )

            body = await request.body()
            if len(body) > self._max_payload_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request payload is too large."},
                )

            async def receive() -> dict[str, object]:
                return {"type": "http.request", "body": body, "more_body": False}

            request._receive = receive

        return await call_next(request)
