import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import IntegrityError, transaction

from apps.payments.models import Payment, IdempotencyRecord
from apps.payments.serializers import PaymentResponseSerializer
from apps.payments.utils import hash_payment_request
from common.errors.exceptions import ConflictException, InternalException


logger = logging.getLogger("payments.service")


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

        logger.info("Processing payment request.")

        # checking idempotency
        try:
            with transaction.atomic():
                record = IdempotencyRecord.objects.create(
                    key=idempotency_key,
                    request_hash=request_hash,
                )
            logger.info("Idempotency key successfully reserved.")

        except IntegrityError as exc:
            # Another request has already reserved this key.
            try:
                record = IdempotencyRecord.objects.select_for_update().get(
                    key=idempotency_key
                )
            except IdempotencyRecord.DoesNotExist:
                logger.exception(
                    "Idempotency record not found after IntegrityError."
                )
                raise InternalException(
                    "Internal server error.",
                    technical_message=(
                        "IntegrityError occurred while creating an idempotency record, "
                        "but no existing record was found for the supplied key."
                    ),
                ) from exc
            except Exception as e:
                logger.exception(
                    "Failed to retrieve existing idempotency record."
                )
                raise InternalException(
                    "Internal server error.",
                    technical_message=str(e),
                ) from e

            logger.info(
                "Duplicate idempotency request detected. Record ID: %s",
                record.pk,
            )

            if record.request_hash != request_hash:
                logger.warning(
                    "Idempotency key reused with a different request payload. "
                    "Record ID: %s",
                    record.pk,
                )
                raise IdempotencyConflict(
                    "Idempotency key was already used with a different request."
                )

            if record.response_status is None or record.response_body is None:
                logger.error(
                    "Incomplete idempotency record detected. Record ID: %s",
                    record.pk,
                )
                raise IncompleteIdempotencyRecord(
                    "Internal server error.",
                    technical_message="Idempotency record exists but has no stored response.",
                )

            # returning stored responses (idempotency)
            logger.info(
                "Replaying previous payment response. "
                "Payment ID: %s, Record ID: %s",
                record.payment_id,
                record.pk,
            )

            return PaymentResult(
                status_code=record.response_status,
                body=record.response_body,
                replayed=True,
            )

        # New idempotency key: create the payment.
        try:
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

        except Exception:
            logger.exception(
                "Payment creation or idempotency response persistence failed."
            )
            raise

        transaction.on_commit(
            lambda: logger.info(
                "Payment transaction committed successfully. "
                "Payment ID: %s, Record ID: %s",
                payment.pk,
                record.pk,
            )
        )

        return PaymentResult(
            status_code=200,
            body=response_body,
            replayed=False,
        )
