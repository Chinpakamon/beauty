import fastapi


class ServiceNotFoundException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )


class ServiceAlreadyExistsException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail="Master already provides this service type",
        )


class ServiceAlreadyActiveException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail="Service is already active",
        )


class ServiceAlreadyInactiveException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail="Service is already inactive",
        )


class ServiceInactiveException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Service is inactive",
        )


class InactiveServiceTypeException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Cannot use inactive service type",
        )


class MasterOnlyException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Services can be assigned only to users with MASTER role",
        )


class MasterIdRequiredException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Admin must provide master_id",
        )
