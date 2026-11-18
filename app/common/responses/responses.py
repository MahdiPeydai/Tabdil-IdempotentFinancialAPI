from typing import Any

from rest_framework import serializers
from rest_framework.response import Response

from common.errors.codes import ResultCode


class ValidationErrorResponseSerializer(serializers.Serializer):
    field = serializers.CharField()
    message = serializers.CharField()


class BaseResponseSerializer(serializers.Serializer):
    result = serializers.JSONField(required=False, allow_null=True)
    success = serializers.BooleanField()
    result_code = serializers.IntegerField()
    error = serializers.CharField(required=False)
    validation_errors = ValidationErrorResponseSerializer(
        many=True,
        required=False,
    )

class SuccessResponseSerializer(BaseResponseSerializer):
    result = serializers.JSONField(required=False, allow_null=True)
    error = serializers.CharField(allow_null=True, required=False, default=None)
    validation_errors = ValidationErrorResponseSerializer(
        many=True,
        allow_null=True,
        required=False,
        default=None,
    )


def success_response(
    result: Any = None,
    status_code: int = 200,
) -> Response:

    data = {
        "result": result,
        "success": True,
        "result_code": ResultCode.SUCCESS,
    }

    serializer = SuccessResponseSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    return Response(
        serializer.data,
        status=status_code,
    )


class ErrorResponseSerializer(serializers.Serializer):
    result = serializers.JSONField(required=False, allow_null=True)
    success = serializers.BooleanField()
    result_code = serializers.IntegerField()
    error = serializers.CharField(required=False)
    validation_errors = ValidationErrorResponseSerializer(
        many=True,
        required=False,
    )