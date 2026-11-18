from rest_framework.test import APITestCase
from django.urls import reverse

from apps.payments.models import Payment, IdempotencyRecord


class PaymentCreateViewTests(APITestCase):

    def setUp(self):
        self.url = reverse("payment-create")

        self.payload = {
            "amount": 100000,
            "currency": "IRR",
            "description": "Test payment",
        }

        self.idempotency_key = "test-key-001"

    def post_payment(self, payload=None, idempotency_key=None):
        return self.client.post(
            self.url,
            payload if payload is not None else self.payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=(
                idempotency_key
                if idempotency_key is not None
                else self.idempotency_key
            ),
        )

    def test_create_payment(self):
        response = self.post_payment()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["result_code"], 0)

        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(IdempotencyRecord.objects.count(), 1)

    def test_same_key_same_payload_returns_original_response(self):
        first_response = self.post_payment()
        second_response = self.post_payment()

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        self.assertEqual(
            first_response.data["result"],
            second_response.data["result"],
        )

        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(IdempotencyRecord.objects.count(), 1)

    def test_same_key_different_payload_returns_conflict(self):
        self.post_payment()

        modified_payload = {
            **self.payload,
            "amount": 200000,
        }

        response = self.post_payment(payload=modified_payload)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(IdempotencyRecord.objects.count(), 1)

    def test_missing_idempotency_key_returns_bad_request(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(IdempotencyRecord.objects.count(), 0)

    def test_zero_amount_returns_bad_request(self):
        payload = {**self.payload, "amount": 0}

        response = self.post_payment(payload=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Payment.objects.count(), 0)

    def test_negative_amount_returns_bad_request(self):
        payload = {**self.payload, "amount": -1000}

        response = self.post_payment(payload=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Payment.objects.count(), 0)

    def test_decimal_amount_returns_bad_request(self):
        payload = {**self.payload, "amount": "1000.5"}

        response = self.post_payment(payload=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Payment.objects.count(), 0)

    def test_invalid_currency_returns_bad_request(self):
        payload = {**self.payload, "currency": "irr"}

        response = self.post_payment(payload=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Payment.objects.count(), 0)

    def test_missing_amount_returns_bad_request(self):
        payload = {
            "currency": "IRR",
            "description": "Test payment",
        }

        response = self.post_payment(payload=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Payment.objects.count(), 0)