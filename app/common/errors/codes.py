from enum import IntEnum


class ResultCode(IntEnum):
    SUCCESS = 0

    CONFLICT_ERROR = 40901

    INTERNAL_ERROR = 50002

    UNEXPECTED_ERROR = 50003