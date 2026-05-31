import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.booking import exceptions, repository, schemas
from app.api.globals import exceptions as global_exceptions
from app.api.globals import repository as global_repository
from app.api.service import exceptions as service_exceptions
from app.api.service import repository as service_repository
from app.api.user import exceptions as user_exceptions
from app.core.database import models


class BookingService:
    TERMINAL_STATUSES = {
        models.BookingStatus.CANCELLED,
        models.BookingStatus.REJECTED,
        models.BookingStatus.COMPLETED,
    }
    MASTER_ALLOWED_STATUSES = {
        models.BookingStatus.CONFIRMED,
        models.BookingStatus.REJECTED,
        models.BookingStatus.CANCELLED,
        models.BookingStatus.COMPLETED,
    }

    @staticmethod
    async def _get_master_or_raise(
        master_id: int,
        session: AsyncSession,
    ) -> models.User:
        master = await global_repository.GloablUserRepository.select_user_by_id(
            user_id=master_id,
            session=session,
        )
        if not master or not master.is_active:
            raise global_exceptions.UserNotFoundException()
        if master.role != models.RoleType.MASTER:
            raise service_exceptions.MasterOnlyException()
        return master

    @staticmethod
    def _ensure_master_owner_or_admin(
        current_user: models.User,
        master_id: int,
    ) -> None:
        if current_user.role == models.RoleType.ADMIN:
            return
        if current_user.role == models.RoleType.MASTER and current_user.id == master_id:
            return
        raise user_exceptions.PermissionDeniedException()

    @staticmethod
    def _resolve_master_id(
        current_user: models.User,
        requested_master_id: int | None,
    ) -> int:
        if current_user.role == models.RoleType.ADMIN:
            if requested_master_id is None:
                raise service_exceptions.MasterIdRequiredException()
            return requested_master_id

        if current_user.role == models.RoleType.MASTER:
            if (
                requested_master_id is not None
                and requested_master_id != current_user.id
            ):
                raise user_exceptions.PermissionDeniedException()
            return current_user.id

        raise user_exceptions.PermissionDeniedException()

    @staticmethod
    async def _get_availability_slot_or_raise(
        slot_id: int,
        session: AsyncSession,
    ) -> models.MasterAvailabilitySlot:
        slot = await repository.BookingRepository.select_availability_slot_by_id(
            slot_id=slot_id,
            session=session,
        )
        if not slot:
            raise exceptions.AvailabilitySlotNotFoundException()
        return slot

    @staticmethod
    async def _get_booking_or_raise(
        booking_id: int,
        session: AsyncSession,
    ) -> models.Booking:
        booking = await repository.BookingRepository.select_booking_by_id(
            booking_id=booking_id,
            session=session,
        )
        if not booking:
            raise exceptions.BookingNotFoundException()
        return booking

    @staticmethod
    def _ensure_booking_participant_or_admin(
        current_user: models.User,
        booking: models.Booking,
    ) -> None:
        if current_user.role == models.RoleType.ADMIN:
            return
        if current_user.id in {booking.user_id, booking.master_id}:
            return
        raise user_exceptions.PermissionDeniedException()

    @staticmethod
    def _ensure_booking_master_or_admin(
        current_user: models.User,
        booking: models.Booking,
    ) -> None:
        if current_user.role == models.RoleType.ADMIN:
            return
        if (
            current_user.role == models.RoleType.MASTER
            and current_user.id == booking.master_id
        ):
            return
        raise user_exceptions.PermissionDeniedException()

    @staticmethod
    async def create_availability_pool(
        data: schemas.CreateAvailabilityPoolRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.CreateAvailabilityPoolResponseSchemas:
        master_id = BookingService._resolve_master_id(
            current_user=current_user,
            requested_master_id=data.master_id,
        )
        await BookingService._get_master_or_raise(master_id=master_id, session=session)

        now = datetime.datetime.now(tz=data.start_time.tzinfo)
        if data.start_time <= now:
            raise exceptions.SlotTimeInPastException()

        slots = []
        for index in range(data.slots_count):
            start_time = data.start_time + datetime.timedelta(
                minutes=data.slot_duration_minutes * index
            )
            existing = (
                await repository.BookingRepository.select_exists_availability_slot(
                    master_id=master_id,
                    start_time=start_time,
                    session=session,
                )
            )
            if existing:
                raise exceptions.AvailabilitySlotAlreadyExistsException()
            slots.append(
                {
                    "master_id": master_id,
                    "start_time": start_time,
                    "end_time": start_time
                    + datetime.timedelta(minutes=data.slot_duration_minutes),
                    "is_booked": False,
                }
            )

        created_slots = await repository.BookingRepository.insert_availability_slots(
            data=slots,
            session=session,
        )
        return schemas.CreateAvailabilityPoolResponseSchemas(
            data=[
                schemas.AvailabilitySlotResponseSchemas(**slot)
                for slot in created_slots
            ]
        )

    @staticmethod
    async def get_master_availability_slots(
        master_id: int,
        data: schemas.ListAvailabilitySlotsRequestSchemas,
        session: AsyncSession,
    ) -> schemas.ListAvailabilitySlotsResponseSchemas:
        await BookingService._get_master_or_raise(master_id=master_id, session=session)
        slots, total = await repository.BookingRepository.select_availability_slots(
            master_id=master_id,
            data=data,
            session=session,
        )
        return schemas.ListAvailabilitySlotsResponseSchemas(
            data=[schemas.AvailabilitySlotResponseSchemas(**slot) for slot in slots],
            total=total,
            limit=data.limit,
            offset=data.offset,
        )

    @staticmethod
    async def create_booking(
        data: schemas.CreateBookingRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.CreateBookingResponseSchemas:
        service = await service_repository.ServiceRepository.select_service_by_id(
            service_id=data.service_id,
            session=session,
        )
        if not service:
            raise service_exceptions.ServiceNotFoundException()
        if not service.is_active:
            raise service_exceptions.ServiceInactiveException()

        if current_user.id == service.master_id:
            raise exceptions.BookingUserCannotBeMasterException()

        slot = await BookingService._get_availability_slot_or_raise(
            slot_id=data.availability_slot_id,
            session=session,
        )
        if slot.master_id != service.master_id:
            raise exceptions.AvailabilitySlotDoesNotBelongToMasterException()
        if slot.is_booked:
            raise exceptions.AvailabilitySlotAlreadyBookedException()

        end_time = slot.start_time + datetime.timedelta(
            minutes=service.duration_minutes
        )
        if end_time > slot.end_time:
            raise exceptions.ServiceDoesNotFitSlotException()

        booking = await repository.BookingRepository.insert_booking(
            data={
                "user_id": current_user.id,
                "service_id": service.id,
                "master_id": service.master_id,
                "availability_slot_id": slot.id,
                "start_time": slot.start_time,
                "end_time": end_time,
                "status": models.BookingStatus.PENDING,
                "comment": data.comment,
            },
            session=session,
        )
        return schemas.CreateBookingResponseSchemas(**booking)

    @staticmethod
    async def get_booking(
        booking_id: int,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.GetBookingResponseSchemas:
        booking = await BookingService._get_booking_or_raise(
            booking_id=booking_id,
            session=session,
        )
        BookingService._ensure_booking_participant_or_admin(
            current_user=current_user,
            booking=booking,
        )
        return schemas.GetBookingResponseSchemas.model_validate(booking)

    @staticmethod
    async def change_booking_status(
        booking_id: int,
        data: schemas.ChangeBookingStatusRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.ChangeBookingStatusResponseSchemas:
        booking = await BookingService._get_booking_or_raise(
            booking_id=booking_id,
            session=session,
        )
        BookingService._ensure_booking_master_or_admin(
            current_user=current_user,
            booking=booking,
        )

        if data.status not in BookingService.MASTER_ALLOWED_STATUSES:
            raise exceptions.BookingCannotBeChangedException()
        if booking.status == data.status:
            raise exceptions.BookingStatusAlreadySetException()
        if booking.status in BookingService.TERMINAL_STATUSES:
            raise exceptions.BookingCannotBeChangedException()

        release_slot = data.status in {
            models.BookingStatus.CANCELLED,
            models.BookingStatus.REJECTED,
        }
        updated_booking = await repository.BookingRepository.update_booking_status(
            booking_id=booking_id,
            status=data.status,
            release_slot=release_slot,
            session=session,
        )
        return schemas.ChangeBookingStatusResponseSchemas(**updated_booking)

    @staticmethod
    async def cancel_booking(
        booking_id: int,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.CancelBookingResponseSchemas:
        booking = await BookingService._get_booking_or_raise(
            booking_id=booking_id,
            session=session,
        )
        BookingService._ensure_booking_participant_or_admin(
            current_user=current_user,
            booking=booking,
        )
        if booking.status in BookingService.TERMINAL_STATUSES:
            raise exceptions.BookingCannotBeChangedException()

        target_status = models.BookingStatus.REJECTED
        if current_user.id == booking.user_id:
            target_status = models.BookingStatus.CANCELLED

        updated_booking = await repository.BookingRepository.update_booking_status(
            booking_id=booking_id,
            status=target_status,
            release_slot=True,
            session=session,
        )
        return schemas.CancelBookingResponseSchemas(**updated_booking)

    @staticmethod
    async def get_booking_list(
        data: schemas.ListBookingsRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.ListBookingsResponseSchemas:
        bookings, total = await repository.BookingRepository.select_bookings(
            data=data,
            current_user=current_user,
            session=session,
        )
        return schemas.ListBookingsResponseSchemas(
            data=[
                schemas.BookingBaseResponseSchemas(**booking) for booking in bookings
            ],
            total=total,
            limit=data.limit,
            offset=data.offset,
        )
