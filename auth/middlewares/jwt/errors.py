from enum import Enum


from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from auth.exceptions import JsonHTTPException

class ErrorObj(BaseModel):
    type: str
    message: str


def json_http_exception_handler(request: Request, exc: JsonHTTPException) -> JSONResponse:
    return JSONResponse(
        content=exc.content,
        status_code=exc.status_code,
    )


def get_error_response(error: ErrorObj, status: int) -> JSONResponse:
    return JSONResponse(
        content={
            'type': error.type,
            'message': error.message,
        },
        status_code=status,
    )


def get_bad_request_error_response(error: ErrorObj) -> JSONResponse:
    return get_error_response(error, status=400)
    

class AccessErrorTypes(str, Enum):
    TOKEN_IS_NOT_SPECIFIED = 'token_is_not_specified'
    INCORRECT_AUTH_HEADER_FORM = 'incorrect_auth_header_form'
    INCORRECT_TOKEN_TYPE = 'incorrect_token_type'
    INVALID_TOKEN = 'invalid_token'
    TOKEN_REVOKED = 'token_revoked'
    TOKEN_ALREADY_REVOKED = 'token_already_revoked'
    TOKEN_OWNER_NOT_FOUND = 'token_owner_not_found'


class AccessError:
    @staticmethod
    def get_token_is_not_specified_error() -> ErrorObj:
        return ErrorObj(
            type=AccessErrorTypes.TOKEN_IS_NOT_SPECIFIED,
            message='Access-token header is not set',
        )

    @staticmethod
    def get_incorrect_auth_header_form_error() -> ErrorObj:
        return ErrorObj(
            type=AccessErrorTypes.INCORRECT_AUTH_HEADER_FORM,
            message='Access-token must have the form "Bearer <TOKEN>"',
        )

    @staticmethod
    def get_incorrect_token_type_error() -> ErrorObj:
        return ErrorObj(
            type=AccessErrorTypes.INCORRECT_TOKEN_TYPE,
            message='The passed token does not match the required type',
        )

    @staticmethod
    def get_invalid_token_error() -> ErrorObj:
        return ErrorObj(
            type=AccessErrorTypes.INVALID_TOKEN,
            message='The transferred token is invalid',
        )

    @staticmethod
    def get_token_revoked_error() -> ErrorObj:
        return ErrorObj(
            type=AccessErrorTypes.TOKEN_REVOKED,
            message='This token has revoked',
        )

    @staticmethod
    def get_token_already_revoked_error() -> ErrorObj:
        return ErrorObj(
            type=AccessErrorTypes.TOKEN_ALREADY_REVOKED,
            message='This token has already been revoked',
        )

    @staticmethod
    def get_token_owner_not_found() -> ErrorObj:
        return ErrorObj(
            type=AccessErrorTypes.TOKEN_OWNER_NOT_FOUND,
            message='The owner of this access token has not been found',
        )