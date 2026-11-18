import uuid

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=0,
        validators=[MinValueValidator(1)],
    )

    currency = models.CharField(
        max_length=3,
        validators=[
            RegexValidator(
                regex=r"^[A-Z]{3}$",
                message="Currency must be a 3-letter uppercase code.",
            )
        ],
    )

    description = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SUCCESS,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.id} - {self.amount} {self.currency}"


class IdempotencyRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    key = models.CharField(max_length=255, unique=True)

    request_hash = models.CharField(max_length=64)

    payment = models.OneToOneField(
        Payment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="idempotency_record",
    )

    response_status = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    response_body = models.JSONField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.key
