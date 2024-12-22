import uuid
import jwt

from src.auth.middlewares.jwt.base.auth import JWTAuth
from src.core.models import IssuedJWTToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def generate_device_id() -> str:
    return str(uuid.uuid4())


async def check_revoked(jti: str, session) -> bool:
    """Check if a token has been revoked"""
    query = select(IssuedJWTToken).filter_by(jti=jti, revoked=True)
    result = await session.execute(query)
    token = result.scalar_one_or_none()
    return token is not None


def try_decode_token(jwt_auth: JWTAuth, token: str):
    try:
        payload = jwt_auth.verify_token(token)
        return payload, None
    except Exception as error:
        return None, error