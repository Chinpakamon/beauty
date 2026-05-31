import fastapi


class BookingNotFoundException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )


class AvailabilitySlotNotFoundException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found",
        )


class AvailabilitySlotAlreadyExistsException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail="Availability slot already exists",
        )


class AvailabilitySlotAlreadyBookedException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail="Availability slot is already booked",
        )


class AvailabilitySlotDoesNotBelongToMasterException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Availability slot does not belong to service master",
        )


class ServiceDoesNotFitSlotException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Service duration does not fit availability slot",
        )


class BookingStatusAlreadySetException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail="Booking already has this status",
        )


class BookingCannotBeChangedException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Booking cannot be changed in its current status",
        )


class BookingUserCannotBeMasterException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Master cannot book own service",
        )


class SlotTimeInPastException(fastapi.HTTPException):
    def __init__(self):
        super().__init__(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Availability slot start time must be in the future",
        )
