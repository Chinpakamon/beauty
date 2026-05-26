from fastapi import HTTPException, Request

from app.api.globals.exceptions import UnauthorizedException


def get_current_user_dep(request: Request):
    current_user = getattr(request.state, "current_user", None)
    if current_user is None:
        raise UnauthorizedException()
    return current_user


def require_admin(request: Request):
    user = request.state.current_user
    if not user or user.role.value != "ADMIN":
        raise HTTPException(
            status_code=403, detail="The user does not have the required rights"
        )
    return user


def require_master_or_admin(request: Request):
    user = request.state.current_user
    if not user or user.role.value not in {"MASTER", "ADMIN"}:
        raise HTTPException(
            status_code=403, detail="The user does not have the required rights"
        )
    return user
