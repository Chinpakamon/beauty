import fastapi


class ReviewNotFoundException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )


class ReviewAlreadyExistsException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail="Review for this booking already exists",
        )


class ReviewBookingNotCompletedException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Review can be created only for completed bookings",
        )
