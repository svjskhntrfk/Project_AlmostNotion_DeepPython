from fastapi import Request, Security
from fastapi.security.api_key import APIKeyHeader
import jwt

from auth.middlewares.jwt.errors import AccessError
from auth.middlewares.jwt.base.token_types import TokenType
from auth.middlewares.jwt.utils import check_revoked
from auth.exceptions import JsonHTTPException
from auth.jwt_settings import jwt_config
from fastapi import Depends
from database import get_user_by_id,get_session
from sqlalchemy.ext.asyncio import AsyncSession


def __try_to_get_clear_token(authorization_header: str) -> str:
    if authorization_header is None:
        raise JsonHTTPException(content=dict(AccessError.get_token_is_not_specified_error()), status_code=400)

    if 'Bearer ' not in authorization_header:
        raise JsonHTTPException(content=dict(AccessError.get_incorrect_auth_header_form_error()), status_code=400)

    return authorization_header.replace('Bearer ', '')


async def check_access_token(
    request: Request,
    authorization_header: str = Security(APIKeyHeader(name='Authorization', auto_error=False)),
    session: AsyncSession = Depends(get_session)
) -> str:
    token = authorization_header or request.cookies.get("Authorization")
    
    clear_token = __try_to_get_clear_token(authorization_header=token)

    try:
        payload = jwt.decode(jwt=clear_token, key=jwt_config.secret, algorithms=['HS256', 'RS256'])
        if payload['type'] != TokenType.ACCESS.value:
            raise JsonHTTPException(content=dict(AccessError.get_incorrect_token_type_error()), status_code=403)
    except Exception:
        raise JsonHTTPException(content=dict(AccessError.get_invalid_token_error()), status_code=403)

    if await check_revoked(payload['jti'], session):
        raise JsonHTTPException(content=dict(AccessError.get_token_revoked_error()), status_code=403)

    try:
        user = await get_user_by_id(id=payload['sub'], session=session)
    except ValueError:
        raise JsonHTTPException(content=dict(AccessError.get_token_owner_not_found()), status_code=403)
    except RuntimeError:
        raise JsonHTTPException(content=dict(AccessError.get_invalid_token_error()), status_code=403)

    if not user:
        raise JsonHTTPException(content=dict(AccessError.get_token_owner_not_found()), status_code=403)

    request.state.user = user
    request.state.device_id = payload['device_id']
    return token
