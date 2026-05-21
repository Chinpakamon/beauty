from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.globals import exceptions as global_exceptions
from app.api.globals import repository as global_repository
from app.core import security
from app.core.database.core import SessionLocal


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.current_user = None
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                payload = security.decode_token(token)
                user_id = int(payload["user_id"])
            except Exception:
                raise global_exceptions.UnauthorizedException()

            async with SessionLocal() as session:
                user = await global_repository.GloablUserRepository.select_user_by_id(
                    user_id=user_id, session=session
                )
                if not user:
                    raise global_exceptions.UserNotFoundException()
                request.state.current_user = user

        return await call_next(request)
