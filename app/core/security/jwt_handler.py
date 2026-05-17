from datetime import datetime, timedelta, timezone

import jwt

from app.core.settings import settings


def create_access_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.access_token_expire_hours
    )
    payload = {**data, "exp": expire}
    return jwt.encode(
        payload=payload, key=settings.jwt_secret, algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> dict:
    return jwt.decode(
        jwt=token, key=settings.jwt_secret, algorithms=settings.jwt_algorithm
    )
