import fastapi


class UserAlreadyExistsException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )


class InvalidCredentialsException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


class PermissionDeniedException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="You do not have sufficient permissions/rights "
            "to perform this operation",
        )


class OldPasswordException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="Invalid old password",
        )


class NewPasswordException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="New password must be different",
        )


class NewEmailMustBeDifferentException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="New email must be different from current",
        )


class RoleAlreadyAssignedException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="Role is already assigned",
        )
