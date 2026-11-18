from common.errors.codes import ResultCode


class AppException(Exception):
    status_code: int = 500
    result_code: ResultCode = ResultCode.INTERNAL_ERROR

    def __init__(
        self,
        message: str,
        *,
        technical_message: str | None = None,
    ):
        self.message = message
        self.technical_message = technical_message

        super().__init__(message)



class ConflictException(AppException):
    status_code = 409
    result_code = ResultCode.CONFLICT_ERROR


class InternalException(AppException):
    status_code = 500
    result_code = ResultCode.INTERNAL_ERROR


class UnexpectedException(AppException):
    status_code = 500
    result_code = ResultCode.UNEXPECTED_ERROR