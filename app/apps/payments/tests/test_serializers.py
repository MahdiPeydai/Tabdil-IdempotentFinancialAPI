from decimal import Decimal

from django.test import TestCase

from apps.payments.models import Payment
from apps.payments.serializers import (
    PaymentCreateSerializer,
    PaymentResponseSerializer,
)


class PaymentCreateSerializerTests(TestCase):
    def test_valid_payload(self):
        serializer = PaymentCreateSerializer(
            data={
                "amount": "150000",
                "currency": "IRR",
                "description": "Order payment",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.assertEqual(
            serializer.validated_data["amount"],
            Decimal("150000"),
        )

    def test_description_is_optional(self):
        serializer = PaymentCreateSerializer(
            data={
                "amount": "100",
                "currency": "USD",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.assertEqual(
            serializer.validated_data["description"],
            "",
        )

    def test_amount_must_be_positive(self):
        serializer = PaymentCreateSerializer(
            data={
                "amount": "0",
                "currency": "USD",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_negative_amount_is_invalid(self):
        serializer = PaymentCreateSerializer(
            data={
                "amount": "-100",
                "currency": "USD",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_amount_with_more_than_two_decimal_places_is_invalid(self):
        serializer = PaymentCreateSerializer(
            data={
                "amount": "100.123",
                "currency": "USD",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_currency_must_be_uppercase(self):
        serializer = PaymentCreateSerializer(
            data={
                "amount": "100",
                "currency": "usd",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("currency", serializer.errors)

    def test_currency_must_contain_only_letters(self):
        serializer = PaymentCreateSerializer(
            data={
                "amount": "100",
                "currency": "U1D",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("currency", serializer.errors)

    def test_currency_must_have_three_characters(self):
        serializer = PaymentCreateSerializer(
            data={
                "amount": "100",
                "currency": "US",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("currency", serializer.errors)

    def test_description_cannot_exceed_255_characters(self):
        serializer = PaymentCreateSerializer(
            data={
                "amount": "100",
                "currency": "USD",
                "description": "a" * 256,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("description", serializer.errors)


class PaymentResponseSerializerTests(TestCase):
    def test_payment_response_fields(self):
        payment = Payment.objects.create(
            amount=Decimal("150000"),
            currency="IRR",
            description="Order payment",
        )

        serializer = PaymentResponseSerializer(payment)

        data = serializer.data

        expected_fields = {
            "id",
            "amount",
            "currency",
            "description",
            "status",
            "created_at",
        }

        self.assertEqual(set(data.keys()), expected_fields)
        self.assertEqual(data["amount"], "150000")
        self.assertEqual(data["currency"], "IRR")
        self.assertEqual(data["status"], Payment.Status.SUCCESS)
