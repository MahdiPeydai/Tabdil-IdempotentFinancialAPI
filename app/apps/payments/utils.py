import hashlib
import json
from decimal import Decimal


def hash_payment_request(*, amount: Decimal, currency: str, description: str) -> str:
    payload = {
        "amount": format(amount.normalize(), "f"),
        "currency": currency,
        "description": description,
    }

    canonical_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()