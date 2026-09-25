import hashlib
import hmac


class HmacSha256Signer:
    """Create HMAC-SHA256 signatures for raw webhook payloads."""

    def __init__(self, secret: str) -> None:
        self._secret = secret

    def sign(self, payload: bytes) -> str:
        return hmac.new(
            self._secret.strip().encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
