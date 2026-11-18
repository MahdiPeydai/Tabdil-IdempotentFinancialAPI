from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.payments.models import Payment, IdempotencyRecord


class PaymentModelTests(TestCase):
    def test_create_payment(self):
        payment = Payment.objects.create(
            amount=Decimal("150000.00"),
            currency="IRR",
            description="Order payment",
        )

        self.assertIsNotNone(payment.id)
        self.assertEqual(payment.amount, Decimal("150000.00"))
        self.assertEqual(payment.currency, "IRR")
        self.assertEqual(payment.status, Payment.Status.SUCCESS)

    def test_payment_default_status_is_success(self):
        payment = Payment.objects.create(
            amount=Decimal("100.00"),
            currency="USD",
        )

        self.assertEqual(payment.status, Payment.Status.SUCCESS)

    def test_payment_amount_must_be_positive(self):
        payment = Payment(
            amount=Decimal("0.00"),
            currency="USD",
        )

        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_payment_currency_must_be_uppercase_three_letters(self):
        payment = Payment(
            amount=Decimal("100.00"),
            currency="usd",
        )

        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_payment_description_can_be_empty(self):
        payment = Payment.objects.create(
            amount=Decimal("100.00"),
            currency="USD",
        )

        self.assertEqual(payment.description, "")


class IdempotencyRecordModelTests(TestCase):
    def test_create_idempotency_record(self):
        record = IdempotencyRecord.objects.create(
            key="request-123",
            request_hash="a" * 64,
        )

        self.assertIsNotNone(record.id)
        self.assertEqual(record.key, "request-123")
        self.assertEqual(record.request_hash, "a" * 64)
        self.assertIsNone(record.payment)
        self.assertIsNone(record.response_status)
        self.assertIsNone(record.response_body)

    def test_idempotency_record_can_be_linked_to_payment(self):
        payment = Payment.objects.create(
            amount=Decimal("200.00"),
            currency="USD",
        )

        record = IdempotencyRecord.objects.create(
            key="request-456",
            request_hash="b" * 64,
            payment=payment,
            response_status=201,
            response_body={"id": str(payment.id), "status": "SUCCESS"},
        )

        self.assertEqual(record.payment, payment)
        self.assertEqual(payment.idempotency_record, record)

    def test_idempotency_record_string_representation(self):
        record = IdempotencyRecord.objects.create(
            key="request-789",
            request_hash="c" * 64,
        )

        self.assertEqual(str(record), "request-789")


class IdempotencyConstraintTests(TestCase):
    def test_idempotency_key_must_be_unique(self):
        IdempotencyRecord.objects.create(
            key="same-key",
            request_hash="a" * 64,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                IdempotencyRecord.objects.create(
                    key="same-key",
                    request_hash="b" * 64,
                )

    def test_payment_can_only_have_one_idempotency_record(self):
        payment = Payment.objects.create(
            amount=Decimal("100.00"),
            currency="USD",
        )

        IdempotencyRecord.objects.create(
            key="key-1",
            request_hash="a" * 64,
            payment=payment,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                IdempotencyRecord.objects.create(
                    key="key-2",
                    request_hash="b" * 64,
                    payment=payment,
                )
