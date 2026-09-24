from starlette.types import ASGIApp, Message, Receive, Scope, Send


class PayloadSizeLimitMiddleware:
    """Reject oversized request bodies before they reach application routes."""

    def __init__(self, app: ASGIApp, max_payload_bytes: int) -> None:
        self._app = app
        self._max_payload_bytes = max_payload_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            await self._app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                if int(content_length) > self._max_payload_bytes:
                    await self._send_rejection(send, 413, b'Request payload is too large.')
                    return
            except ValueError:
                await self._send_rejection(send, 400, b'Invalid Content-Length header.')
                return

        consumed = 0

        async def limited_receive() -> Message:
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > self._max_payload_bytes:
                    return {
                        "type": "http.disconnect",
                    }
            return message

        try:
            await self._app(scope, limited_receive, send)
        except RuntimeError as exc:
            if consumed <= self._max_payload_bytes:
                raise
            await self._send_rejection(send, 413, b'Request payload is too large.')

    async def _send_rejection(self, send: Send, status: int, detail: bytes) -> None:
        body = b'{"detail":"' + detail + b'"}'
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
