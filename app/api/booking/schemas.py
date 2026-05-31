import datetime

import pydantic

from app.api.booking import consts
from app.core.database import models


class AvailabilitySlotResponseSchemas(pydantic.BaseModel):
    id: int
    master_id: int
    start_time: datetime.datetime
    end_time: datetime.datetime
    is_booked: bool

    model_config = pydantic.ConfigDict(from_attributes=True)


class CreateAvailabilityPoolRequestSchemas(pydantic.BaseModel):
    start_time: datetime.datetime
    slot_duration_minutes: int = pydantic.Field(gt=0, le=24 * 60)
    slots_count: int = pydantic.Field(gt=0, le=96)
    master_id: int | None = None


class CreateAvailabilityPoolResponseSchemas(pydantic.BaseModel):
    data: list[AvailabilitySlotResponseSchemas]


class ListAvailabilitySlotsFilters(pydantic.BaseModel):
    date_from: datetime.datetime | None = None
    date_to: datetime.datetime | None = None
    include_booked: bool = False


class ListAvailabilitySlotsRequestSchemas(pydantic.BaseModel):
    filters: ListAvailabilitySlotsFilters | None = None
    limit: int = pydantic.Field(default=50, ge=1, le=200)
    offset: int = pydantic.Field(default=0, ge=0)


class ListAvailabilitySlotsResponseSchemas(pydantic.BaseModel):
    data: list[AvailabilitySlotResponseSchemas]
    total: int
    limit: int
    offset: int


class BookingBaseResponseSchemas(pydantic.BaseModel):
    id: int
    user_id: int
    service_id: int
    master_id: int
    availability_slot_id: int
    start_time: datetime.datetime
    end_time: datetime.datetime
    status: models.BookingStatus
    comment: str | None

    model_config = pydantic.ConfigDict(from_attributes=True)


class CreateBookingRequestSchemas(pydantic.BaseModel):
    service_id: int
    availability_slot_id: int
    comment: str | None = pydantic.Field(default=None, max_length=1000)


class CreateBookingResponseSchemas(BookingBaseResponseSchemas): ...


class ChangeBookingStatusRequestSchemas(pydantic.BaseModel):
    status: models.BookingStatus


class ChangeBookingStatusResponseSchemas(BookingBaseResponseSchemas): ...


class CancelBookingResponseSchemas(BookingBaseResponseSchemas): ...


class GetBookingResponseSchemas(BookingBaseResponseSchemas): ...


class ListBookingsFilters(pydantic.BaseModel):
    status: models.BookingStatus | None = None


class ListBookingsRequestSchemas(pydantic.BaseModel):
    filters: ListBookingsFilters | None = None
    order_by: consts.BookingOrderByType | None = (
        consts.BookingOrderByType.CREATED_AT_DESC
    )
    limit: int = pydantic.Field(default=10, ge=1, le=100)
    offset: int = pydantic.Field(default=0, ge=0)


class ListBookingsResponseSchemas(pydantic.BaseModel):
    data: list[BookingBaseResponseSchemas]
    total: int
    limit: int
    offset: int
