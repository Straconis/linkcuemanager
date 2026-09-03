import time
import uuid

from app.linkcue_identity import LinkCueIdentity


def create_signed_headers(
    identity: LinkCueIdentity,
    *,
    method: str,
    path: str,
    body: bytes = b"",
) -> dict[str, str]:
    from app.client_auth import sign_request

    timestamp = int(time.time())
    nonce = uuid.uuid4().hex

    signature = sign_request(
        secret=identity.secret,
        client_id=identity.client_id,
        timestamp=timestamp,
        nonce=nonce,
        method=method,
        path=path,
        body=body,
    )

    return {
        "X-LinkCue-Client": identity.client_id,
        "X-LinkCue-Timestamp": str(timestamp),
        "X-LinkCue-Nonce": nonce,
        "X-LinkCue-Signature": signature,
    }
