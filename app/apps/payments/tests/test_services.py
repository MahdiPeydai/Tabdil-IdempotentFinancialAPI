from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase

from apps.payments.models import Payment, IdempotencyRecord
from apps.payments.services import (
    PaymentService,
    IdempotencyConflict,
    IncompleteIdempotencyRecord,
)
from common.errors.exceptions import InternalException


class PaymentServiceTests(TestCase):

    def setUp(self):
        self.payload = {
            "idempotency_key": "test-key-001",
            "amount": Decimal("100000"),
            "currency": "IRR",
            "description": "Test payment",
        }

    def test_create_payment(self):
        result = PaymentService.create(**self.payload)

        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.replayed)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(IdempotencyRecord.objects.count(), 1)

        record = IdempotencyRecord.objects.get(
            key=self.payload["idempotency_key"]
        )

        self.assertEqual(record.response_status, 200)
        self.assertEqual(record.payment_id, Payment.objects.first().id)

    def test_same_key_same_payload_returns_original_response(self):
        first_result = PaymentService.create(**self.payload)
        second_result = PaymentService.create(**self.payload)

        self.assertEqual(first_result.status_code, 200)
        self.assertEqual(second_result.status_code, 200)

        self.assertFalse(first_result.replayed)
        self.assertTrue(second_result.replayed)

        self.assertEqual(first_result.body, second_result.body)
        self.assertEqual(Payment.objects.count(), 1)

    def test_same_key_different_payload_raises_conflict(self):
        PaymentService.create(**self.payload)

        modified_payload = {
            **self.payload,
            "amount": Decimal("200000"),
        }

        with self.assertRaises(IdempotencyConflict):
            PaymentService.create(**modified_payload)

        self.assertEqual(Payment.objects.count(), 1)

    def test_different_keys_create_different_payments(self):
        PaymentService.create(**self.payload)

        another_payload = {
            **self.payload,
            "idempotency_key": "test-key-002",
        }

        result = PaymentService.create(**another_payload)

        self.assertFalse(result.replayed)
        self.assertEqual(Payment.objects.count(), 2)
        self.assertEqual(IdempotencyRecord.objects.count(), 2)

    def test_incomplete_record_raises_exception(self):
        IdempotencyRecord.objects.create(
            key=self.payload["idempotency_key"],
            request_hash="some-hash",
        )

        # Use the same hash as the existing record.
        from apps.payments.utils import hash_payment_request

        request_hash = hash_payment_request(
            amount=self.payload["amount"],
            currency=self.payload["currency"],
            description=self.payload["description"],
        )

        record = IdempotencyRecord.objects.get(
            key=self.payload["idempotency_key"]
        )
        record.request_hash = request_hash
        record.save(update_fields=["request_hash"])

        with self.assertRaises(IncompleteIdempotencyRecord):
            PaymentService.create(**self.payload)

        self.assertEqual(Payment.objects.count(), 0)

    @patch("apps.payments.services.IdempotencyRecord.objects.select_for_update")
    @patch("apps.payments.services.IdempotencyRecord.objects.create")
    def test_integrity_error_without_existing_record_raises_internal_exception(self, mock_create, mock_select_for_update):
        mock_create.side_effect = IntegrityError("Unique constraint violation")
        mock_select_for_update.return_value.get.side_effect = (
            IdempotencyRecord.DoesNotExist
        )

        with self.assertRaises(InternalException) as context:
            PaymentService.create(**self.payload)

        self.assertEqual(
            context.exception.message,
            "Internal server error.",
        )

        self.assertIsInstance(
            context.exception.__cause__,
            IntegrityError,
        )

    @patch("apps.payments.services.IdempotencyRecord.objects.select_for_update")
    @patch("apps.payments.services.IdempotencyRecord.objects.create")
    def test_unexpected_lookup_error_raises_internal_exception(self, mock_create, mock_select_for_update):
        mock_create.side_effect = IntegrityError("Database error")
        mock_select_for_update.return_value.get.side_effect = RuntimeError(
            "Unexpected database error"
        )

        with self.assertRaises(InternalException) as context:
            PaymentService.create(**self.payload)

        self.assertEqual(
            context.exception.message,
            "Internal server error.",
        )

        self.assertEqual(
            context.exception.technical_message,
            "Unexpected database error",
        )
