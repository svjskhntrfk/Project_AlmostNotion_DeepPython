import jwt
import uuid
from typing import Any
from datetime import datetime, timedelta, timezone

from .config import JWTConfig
from .token_types import TokenType
from calendar import timegm
from datetime import datetime
from hashlib import sha256


def convert_to_timestamp(datetime: datetime) -> int:
    return timegm(datetime.utctimetuple())


def get_sha256_hash(line: str) -> str:
    return sha256(str.encode(line)).hexdigest()


class JWTAuth:
    def __init__(self, config: JWTConfig) -> None:
        self._config = config

    def generate_unlimited_access_token(self, subject: str, payload: dict[str, Any] = {}) -> str:
        return self.__sign_token(type=TokenType.ACCESS.value, subject=subject, payload=payload)

    def generate_access_token(self, subject: str, payload: dict[str, Any] = {}) -> str:
        return self.__sign_token(
            type=TokenType.ACCESS.value,
            subject=subject,
            payload=payload,
            ttl=self._config.access_token_ttl,
        )

    def generate_refresh_token(self, subject: str, payload: dict[str, Any] = {}) -> str:
        return self.__sign_token(
            type=TokenType.REFRESH.value,
            subject=subject,
            payload=payload,
            ttl=self._config.refresh_token_ttl,
        )

    def __sign_token(self, type: str, subject: str, payload: dict[str, Any] = {}, ttl: timedelta = None) -> str:
        current_timestamp = convert_to_timestamp(datetime.now(tz=timezone.utc))

        data = dict(
            iss='befunny@auth_service',
            sub=subject,
            type=type,
            jti=self.__generate_jti(),
            iat=current_timestamp,
            nbf=payload['nbf'] if payload.get('nbf') else current_timestamp,
        )
        data.update(dict(exp=data['nbf'] + int(ttl.total_seconds()))) if ttl else None
        payload.update(data)
        return jwt.encode(payload, self._config.secret, algorithm=self._config.algorithm)

    @staticmethod
    def __generate_jti() -> str:
        return str(uuid.uuid4())

    def verify_token(self, token) -> dict[str, Any]:
        return jwt.decode(token, self._config.secret, algorithms=[self._config.algorithm])

    def get_jti(self, token) -> str:
        return self.verify_token(token)['jti']

    def get_sub(self, token) -> str:
        return self.verify_token(token)['sub']

    def get_exp(self, token) -> int:
        return self.verify_token(token)['exp']

    @staticmethod
    def get_raw_jwt(token) -> dict[str, Any]:
        """
        Return the payload of the token without checking the validity of the token
        """
        return jwt.decode(token, options={'verify_signature': False})