from rest_framework.exceptions import ValidationError


class IdempotencyKeyMixin:

    def get_idempotency_key(self, request):
        key = request.headers.get("Idempotency-Key")

        if not key:
            raise ValidationError({
                "Idempotency-Key": ["This header is required."]
            })

        return key