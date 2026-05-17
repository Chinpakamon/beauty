import fastapi


class DatabaseException(Exception):
    """Ошибка работы с базой данных."""


class UnauthorizedException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )


class UserNotFoundException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_404_NOT_FOUND, detail="User not found"
        )
