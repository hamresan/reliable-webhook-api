import hashlib
import hmac

import pytest

from reliable_webhook_api.infrastructure.security import HmacSha256SignatureVerifier


@pytest.mark.parametrize(
    ("secret", "payload", "expected"),
    [
        (
            "key",
            b"The quick brown fox jumps over the lazy dog",
            "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8",
        ),
        (
            "secret",
            b'{"event_id":"00000000-0000-0000-0000-000000000001"}',
            hmac.new(
                b"secret",
                b'{"event_id":"00000000-0000-0000-0000-000000000001"}',
                hashlib.sha256,
            ).hexdigest(),
        ),
    ],
)
def test_verify_accepts_known_hmac_sha256_vectors(
    secret: str,
    payload: bytes,
    expected: str,
) -> None:
    verifier = HmacSha256SignatureVerifier(secret)

    assert verifier.verify(payload, expected)


def test_verify_rejects_invalid_signature() -> None:
    verifier = HmacSha256SignatureVerifier("secret")

    assert not verifier.verify(b"payload", "0" * 64)


@pytest.mark.parametrize("signature", ["", "abc", "g" * 64, "12" * 31])
def test_verify_rejects_malformed_signature(signature: str) -> None:
    verifier = HmacSha256SignatureVerifier("secret")

    assert not verifier.verify(b"payload", signature)


def test_verify_fails_closed_when_secret_is_missing() -> None:
    verifier = HmacSha256SignatureVerifier("   ")

    assert not verifier.verify(b"payload", "0" * 64)
