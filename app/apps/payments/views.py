from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.payments.mixins import IdempotencyKeyMixin
from apps.payments.serializers import PaymentCreateSerializer, PaymentSuccessResponseSerializer
from apps.payments.services import PaymentService
from common.responses.responses import success_response, ErrorResponseSerializer


class PaymentCreateView(IdempotencyKeyMixin, APIView):
    @extend_schema(
        summary="Create a payment",
        description=(
                "Creates a payment using an idempotency key. "
                "Repeating the same request with the same key returns "
                "the original response. Reusing the key with a different "
                "payload returns a conflict."
        ),
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Unique key identifying this payment operation.",
            ),
        ],
        request=PaymentCreateSerializer,
        responses={
            200: PaymentSuccessResponseSerializer,
            400: ErrorResponseSerializer,
            409: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        idempotency_key = self.get_idempotency_key(request)

        # validate request body
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # business logic
        result = PaymentService.create(
            idempotency_key=idempotency_key,
            **serializer.validated_data,
        )

        return success_response(
            result=result.body,
            status_code=result.status_code,
        )
