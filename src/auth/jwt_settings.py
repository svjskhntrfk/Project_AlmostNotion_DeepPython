from environs import Env
from datetime import timedelta
from fastapi import FastAPI

from src.auth.middlewares.jwt.base.config import JWTConfig


env = Env()
env.read_env()

API_SECRET = env('API_SECRET')
HASH_SALT = env('HASH_SALT')

JWT_SECRET = env('JWT_SECRET')
ACCESS_TOKEN_TTL = env.int('ACCESS_TOKEN_TTL')
REFRESH_TOKEN_TTL = env.int('REFRESH_TOKEN_TTL')
jwt_config = JWTConfig(
    secret=JWT_SECRET,
    access_token_ttl=timedelta(seconds=ACCESS_TOKEN_TTL),
    refresh_token_ttl=timedelta(seconds=REFRESH_TOKEN_TTL),
)

