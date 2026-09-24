from typing import Protocol


class SignatureVerifier(Protocol):
    def verify(self, payload: bytes, signature: str) -> bool: ...
