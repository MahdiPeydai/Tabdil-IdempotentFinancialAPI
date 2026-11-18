import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from common.errors.codes import ResultCode
from common.errors.exceptions import AppException


logger = logging.getLogger(__name__)


def flatten_validation_errors(errors, prefix="") -> list[dict]:
    result = []

    if isinstance(errors, dict):
        for field, messages in errors.items():
            field_path = f"{prefix}.{field}" if prefix else str(field)
            result.extend(
                flatten_validation_errors(messages, field_path)
            )

    elif isinstance(errors, list):
        for item in errors:
            if isinstance(item, (dict, list)):
                result.extend(
                    flatten_validation_errors(item, prefix)
                )
            else:
                result.append({
                    "field": prefix,
                    "message": str(item),
                })

    else:
        result.append({
            "field": prefix,
            "message": str(errors),
        })

    return result


def custom_exception_handler(exc, context):
    # 1. Application exceptions
    if isinstance(exc, AppException):
        logger.warning(
            "Application error: %s",
            exc.technical_message or exc.message,
        )

        body = {
            "result": None,
            "success": False,
            "result_code": int(exc.result_code),
            "error": exc.message,
        }

        if hasattr(exc, "validation_errors") and exc.validation_errors:
            body["validation_errors"] = exc.validation_errors

        return Response(body, status=exc.status_code)

    # 2. DRF and Django exceptions
    response = exception_handler(exc, context)

    if response is not None:
        error_code = ResultCode.INTERNAL_ERROR

        if response.status_code == status.HTTP_409_CONFLICT:
            error_code = ResultCode.CONFLICT_ERROR


        body = {
            "result": None,
            "success": False,
            "result_code": int(error_code),
            "error": "Request validation failed."
            if response.status_code == 400
            else "Request failed.",
        }

        if response.status_code == 400:
            body["validation_errors"] = flatten_validation_errors(response.data)

        return Response(body, status=response.status_code)

    # 3. Unexpected exceptions
    logger.exception(
        "Unhandled exception",
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return Response(
        {
            "result": None,
            "success": False,
            "result_code": int(ResultCode.UNEXPECTED_ERROR),
            "error": "Internal server error.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
