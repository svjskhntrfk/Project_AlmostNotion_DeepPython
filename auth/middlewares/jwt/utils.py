import uuid
import jwt

from auth.middlewares.jwt.base.auth import JWTAuth
from models import IssuedJWTToken


def generate_device_id() -> str:
    return str(uuid.uuid4())


async def check_revoked(jti: str) -> bool:
    return await IssuedJWTToken.filter(jti=jti, revoked=True).exists()


def try_decode_token(jwt_auth: JWTAuth, token: str):
    try:
        payload = jwt_auth.verify_token(token)
        return payload, None
    except Exception as error:
        return None, error