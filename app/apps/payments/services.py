from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import IntegrityError, transaction

from apps.payments.models import Payment, IdempotencyRecord
from apps.payments.serializers import PaymentResponseSerializer
from apps.payments.utils import hash_payment_request
from common.errors.exceptions import ConflictException, InternalException


class IdempotencyConflict(ConflictException):
    pass

class IncompleteIdempotencyRecord(InternalException):
    pass


@dataclass(frozen=True)
class PaymentResult:
    status_code: int
    body: dict[str, Any]
    replayed: bool


class PaymentService:
    @staticmethod
    @transaction.atomic
    def create(*, idempotency_key: str, amount: Decimal, currency: str, description: str = "") -> PaymentResult:

        request_hash = hash_payment_request(amount=amount, currency=currency, description=description)

        # checking idempotency
        try:
            with transaction.atomic():
                record = IdempotencyRecord.objects.create(
                    key=idempotency_key,
                    request_hash=request_hash,
                )

        except IntegrityError as exc:
            # Another request has already reserved this key.
            try:
                record = IdempotencyRecord.objects.select_for_update().get(
                    key=idempotency_key
                )
            except IdempotencyRecord.DoesNotExist:
                raise InternalException(
                    "Internal server error.",
                    technical_message=(
                        "IntegrityError occurred while creating an idempotency record, "
                        "but no existing record was found for the supplied key."
                    ),
                ) from exc
            except Exception as e:
                raise InternalException(
                    "Internal server error.",
                    technical_message=str(e),
                ) from e

            if record.request_hash != request_hash:
                raise IdempotencyConflict(
                    "Idempotency key was already used with a different request."
                )

            if record.response_status is None or record.response_body is None:
                raise IncompleteIdempotencyRecord(
                    "Internal server error.",
                    technical_message="Idempotency record exists but has no stored response.",
                )

            # returning stored responses (idempotency)
            return PaymentResult(
                status_code=record.response_status,
                body=record.response_body,
                replayed=True,
            )

        # New idempotency key: create the payment.
        payment = Payment.objects.create(
            amount=amount,
            currency=currency,
            description=description,
        )

        response_body = dict(PaymentResponseSerializer(payment).data)

        # Store the original responses.
        record.payment = payment
        record.response_status = 200
        record.response_body = response_body

        record.save(
            update_fields=[
                "payment",
                "response_status",
                "response_body",
            ]
        )

        return PaymentResult(
            status_code=200,
            body=response_body,
            replayed=False,
        )
