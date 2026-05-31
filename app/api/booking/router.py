from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.booking import schemas, service
from app.core.database.core import get_session
from app.core.middleware import dependencies

router = APIRouter(prefix="/booking", tags=["Booking"])


@router.post(
    "/availability/pool",
    response_model=schemas.CreateAvailabilityPoolResponseSchemas,
)
async def create_availability_pool(
    data: schemas.CreateAvailabilityPoolRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_master_or_admin),
):
    return await service.BookingService.create_availability_pool(
        data=data,
        current_user=current_user,
        session=session,
    )


@router.get(
    "/availability/{master_id:int}",
    response_model=schemas.ListAvailabilitySlotsResponseSchemas,
)
async def get_master_availability_slots(
    master_id: int,
    data: schemas.ListAvailabilitySlotsRequestSchemas = Body(
        default=schemas.ListAvailabilitySlotsRequestSchemas()
    ),
    session: AsyncSession = Depends(get_session),
):
    return await service.BookingService.get_master_availability_slots(
        master_id=master_id,
        data=data,
        session=session,
    )


@router.post("/create", response_model=schemas.CreateBookingResponseSchemas)
async def create_booking(
    data: schemas.CreateBookingRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.get_current_user_dep),
):
    return await service.BookingService.create_booking(
        data=data,
        current_user=current_user,
        session=session,
    )


@router.get("/{booking_id:int}", response_model=schemas.GetBookingResponseSchemas)
async def get_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.get_current_user_dep),
):
    return await service.BookingService.get_booking(
        booking_id=booking_id,
        current_user=current_user,
        session=session,
    )


@router.patch(
    "/change-status/{booking_id:int}",
    response_model=schemas.ChangeBookingStatusResponseSchemas,
)
async def change_booking_status(
    booking_id: int,
    data: schemas.ChangeBookingStatusRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_master_or_admin),
):
    return await service.BookingService.change_booking_status(
        booking_id=booking_id,
        data=data,
        current_user=current_user,
        session=session,
    )


@router.patch(
    "/cancel/{booking_id:int}", response_model=schemas.CancelBookingResponseSchemas
)
async def cancel_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.get_current_user_dep),
):
    return await service.BookingService.cancel_booking(
        booking_id=booking_id,
        current_user=current_user,
        session=session,
    )


@router.get("/list", response_model=schemas.ListBookingsResponseSchemas)
async def booking_list(
    data: schemas.ListBookingsRequestSchemas = Body(),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.get_current_user_dep),
):
    return await service.BookingService.get_booking_list(
        data=data,
        current_user=current_user,
        session=session,
    )
