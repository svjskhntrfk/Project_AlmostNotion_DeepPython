from models import User
from auth.middlewares.jwt.base.auth import JWTAuth
from auth.middlewares.jwt.base.token_types import TokenType
from auth.middlewares.jwt.errors import AccessError
from auth.middlewares.jwt.utils import check_revoked, generate_device_id, try_decode_token
from auth.errors import AuthError
from models import IssuedJWTToken
from auth.dto import TokensDTO, UserCredentialsDTO
from hashlib import sha256
from sqlalchemy.ext.asyncio import AsyncSession
from database import create_user, is_email_registered, create_jwt_tokens

def get_sha256_hash(line: str) -> str:
    return sha256(str.encode(line)).hexdigest()

from pydantic import BaseModel

class ErrorObj(BaseModel):
    type: str
    message: str


class AuthService:
    def __init__(self, jwt_auth: JWTAuth) -> None:
        self._jwt_auth = jwt_auth

    async def register(self, body: UserCredentialsDTO, username: str, session: AsyncSession) -> tuple[TokensDTO, None] | tuple[None, ErrorObj]:
        if await is_email_registered(email=body.email, session=session):
            return None, AuthError.get_email_occupied_error()

        user_dict = {
            "email": body.email,
            "username": username,
            "password": get_sha256_hash(body.password)
        }
        await create_user(**user_dict, session=session)
        user = await is_email_registered(email=body.email, session=session)
        print(user)

        access_token, refresh_token = await self._issue_tokens_for_user(user=user, session=session)

        print(access_token  , refresh_token)
        return TokensDTO(access_token=access_token, refresh_token=refresh_token), None

    async def login(self, body: UserCredentialsDTO, session: AsyncSession) -> tuple[TokensDTO, None] | tuple[None, ErrorObj]:
        user = await is_email_registered(email=body.email, session=session)
        if not user or user.password != get_sha256_hash(body.password):
            return None, AuthError.get_invalid_credentials_error()

        access_token, refresh_token = await self._issue_tokens_for_user(user=user, session=session)

        return TokensDTO(access_token=access_token, refresh_token=refresh_token), None

    async def logout(self, user: User, device_id: str, session: AsyncSession) -> None:
        await user.tokens.filter(device_id=device_id).update(revoked=True)

    async def update_tokens(self, user: User, refresh_token: str, session: AsyncSession) -> tuple[TokensDTO, None] | tuple[None, ErrorObj]:
        payload, error = try_decode_token(jwt_auth=self._jwt_auth, token=refresh_token)

        if error:
            return None, AccessError.get_invalid_token_error()

        if payload['type'] != TokenType.REFRESH.value:
            return None, AccessError.get_incorrect_token_type_error()

        user = await User.filter(id=payload['sub']).first()

        # Если обновленный токен пробуют обновить ещё раз,
        # нужно отменить все выущенные на пользователя токены и вернуть ошибку
        if await check_revoked(payload['jti']):
            await IssuedJWTToken.filter(subject=user).update(revoked=True)
            return None, AccessError.get_token_already_revoked_error()

        device_id = payload['device_id']
        await IssuedJWTToken.filter(subject=user, device_id=device_id).update(revoked=True)

        access_token, refresh_token = await self._issue_tokens_for_user(user, device_id, session)

        return TokensDTO(access_token=access_token, refresh_token=refresh_token), None

    async def _issue_tokens_for_user(self, user: User, device_id: str, session: AsyncSession) -> tuple[str, str]:
        print('started creating tokens')
        access_token = self._jwt_auth.generate_access_token(subject=str(user.id), payload={'device_id': device_id})
        refresh_token = self._jwt_auth.generate_refresh_token(subject=str(user.id), payload={'device_id': device_id})

        raw_tokens = [self._jwt_auth.get_raw_jwt(token) for token in [access_token, refresh_token]]
        
        await create_jwt_tokens(raw_tokens, user, device_id, session)
        
        print('tokens created')
        print(access_token, refresh_token)
        return access_token, refresh_token