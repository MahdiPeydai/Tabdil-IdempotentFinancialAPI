from rest_framework import serializers

from apps.payments.models import Payment
from common.responses.responses import SuccessResponseSerializer


class PaymentCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=0,
        min_value=1,
    )

    currency = serializers.CharField(
        max_length=3,
    )

    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
    )

    def validate_currency(self, value):
        if not value.isupper() or len(value) != 3 or not value.isalpha():
            raise serializers.ValidationError(
                "Currency must be a 3-letter uppercase code."
            )

        return value


class PaymentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "currency",
            "description",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class PaymentSuccessResponseSerializer(SuccessResponseSerializer):
    result = PaymentResponseSerializer()
