import hashlib
import hmac

from reliable_webhook_api.application.ports import SignatureVerifier


class HmacSha256SignatureVerifier(SignatureVerifier):
    def __init__(self, secret: str) -> None:
        self._secret = secret

    def verify(self, payload: bytes, signature: str) -> bool:
        secret = self._secret.strip()
        candidate = signature.strip().lower()

        if not secret or len(candidate) != 64:
            return False

        try:
            bytes.fromhex(candidate)
        except ValueError:
            return False

        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, candidate)
