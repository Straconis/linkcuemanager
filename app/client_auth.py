import hashlib
import hmac


SIGNATURE_VERSION = "v1"


def body_digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def canonical_request(
    *,
    client_id: str,
    timestamp: int,
    nonce: str,
    method: str,
    path: str,
    body: bytes,
) -> bytes:
    parts = (
        SIGNATURE_VERSION,
        client_id,
        str(timestamp),
        nonce,
        method.upper(),
        path,
        body_digest(body),
    )

    return "\n".join(parts).encode("utf-8")


def sign_request(
    *,
    secret: str,
    client_id: str,
    timestamp: int,
    nonce: str,
    method: str,
    path: str,
    body: bytes = b"",
) -> str:
    message = canonical_request(
        client_id=client_id,
        timestamp=timestamp,
        nonce=nonce,
        method=method,
        path=path,
        body=body,
    )

    return hmac.new(
        bytes.fromhex(secret),
        message,
        hashlib.sha256,
    ).hexdigest()
