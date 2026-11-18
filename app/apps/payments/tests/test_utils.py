from decimal import Decimal

from django.test import TestCase

from apps.payments.utils import hash_payment_request


class TestHashPaymentRequest(TestCase):

    def test_returns_sha256_hex_digest(self):
        result = hash_payment_request(
            amount=Decimal("100.00"),
            currency="IRR",
            description="Test payment",
        )

        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_input_returns_same_hash(self):
        kwargs = {
            "amount": Decimal("100.00"),
            "currency": "IRR",
            "description": "Test payment",
        }

        first = hash_payment_request(**kwargs)
        second = hash_payment_request(**kwargs)

        assert first == second

    def test_different_amount_returns_different_hash(self):
        first = hash_payment_request(
            amount=Decimal("100.00"),
            currency="IRR",
            description="Test payment",
        )
        second = hash_payment_request(
            amount=Decimal("200.00"),
            currency="IRR",
            description="Test payment",
        )

        assert first != second

    def test_different_currency_returns_different_hash(self):
        first = hash_payment_request(
            amount=Decimal("100.00"),
            currency="IRR",
            description="Test payment",
        )
        second = hash_payment_request(
            amount=Decimal("100.00"),
            currency="USD",
            description="Test payment",
        )

        assert first != second

    def test_different_description_returns_different_hash(self):
        first = hash_payment_request(
            amount=Decimal("100.00"),
            currency="IRR",
            description="Payment A",
        )
        second = hash_payment_request(
            amount=Decimal("100.00"),
            currency="IRR",
            description="Payment B",
        )

        assert first != second

    def test_decimal_trailing_zeros_produce_same_hash(self):
        first = hash_payment_request(
            amount=Decimal("100.0"),
            currency="IRR",
            description="Test payment",
        )
        second = hash_payment_request(
            amount=Decimal("100.00"),
            currency="IRR",
            description="Test payment",
        )

        assert first == second
