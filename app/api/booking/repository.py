import datetime
import logging

import sqlalchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.booking import consts, schemas
from app.api.globals import exceptions as global_exceptions
from app.core.database import models

logger = logging.getLogger(__name__)


class BookingRepository:
    @staticmethod
    async def insert_availability_slots(
        data: list[dict],
        session: AsyncSession,
    ) -> list[sqlalchemy.RowMapping]:
        query = (
            sqlalchemy.insert(models.MasterAvailabilitySlot)
            .values(data)
            .returning(
                models.MasterAvailabilitySlot.id,
                models.MasterAvailabilitySlot.master_id,
                models.MasterAvailabilitySlot.start_time,
                models.MasterAvailabilitySlot.end_time,
                models.MasterAvailabilitySlot.is_booked,
            )
        )

        try:
            result = await session.execute(query)
            await session.commit()
            return list(result.mappings().all())
        except IntegrityError as e:
            await session.rollback()
            logger.warning("Integrity error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Integrity error")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")

    @staticmethod
    async def select_availability_slot_by_id(
        slot_id: int,
        session: AsyncSession,
    ) -> models.MasterAvailabilitySlot | None:
        query = sqlalchemy.select(models.MasterAvailabilitySlot).where(
            models.MasterAvailabilitySlot.id == slot_id
        )
        return await session.scalar(query)

    @staticmethod
    async def select_exists_availability_slot(
        master_id: int,
        start_time: datetime.datetime,
        session: AsyncSession,
    ) -> bool:
        query = sqlalchemy.select(
            sqlalchemy.exists().where(
                sqlalchemy.and_(
                    models.MasterAvailabilitySlot.master_id == master_id,
                    models.MasterAvailabilitySlot.start_time == start_time,
                )
            )
        )
        result = await session.execute(query)
        return result.scalar()

    @staticmethod
    def availability_slots_filter(
        query: sqlalchemy.Select,
        master_id: int,
        data: schemas.ListAvailabilitySlotsRequestSchemas,
    ) -> sqlalchemy.Select:
        query = query.where(models.MasterAvailabilitySlot.master_id == master_id)

        include_booked = False
        if data.filters:
            include_booked = data.filters.include_booked
            if data.filters.date_from is not None:
                query = query.where(
                    models.MasterAvailabilitySlot.start_time >= data.filters.date_from
                )
            if data.filters.date_to is not None:
                query = query.where(
                    models.MasterAvailabilitySlot.start_time <= data.filters.date_to
                )

        if not include_booked:
            query = query.where(models.MasterAvailabilitySlot.is_booked.is_(False))

        return query

    @staticmethod
    async def select_availability_slots(
        master_id: int,
        data: schemas.ListAvailabilitySlotsRequestSchemas,
        session: AsyncSession,
    ) -> tuple[list[sqlalchemy.RowMapping], int]:
        query = sqlalchemy.select(
            models.MasterAvailabilitySlot.id,
            models.MasterAvailabilitySlot.master_id,
            models.MasterAvailabilitySlot.start_time,
            models.MasterAvailabilitySlot.end_time,
            models.MasterAvailabilitySlot.is_booked,
        )
        query = BookingRepository.availability_slots_filter(
            query=query, master_id=master_id, data=data
        )

        count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(
            query.subquery()
        )
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        query = query.order_by(models.MasterAvailabilitySlot.start_time.asc())
        query = query.limit(data.limit).offset(data.offset)

        try:
            result = await session.execute(query)
            return list(result.mappings().all()), total
        except SQLAlchemyError as e:
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")

    @staticmethod
    async def insert_booking(
        data: dict,
        session: AsyncSession,
    ) -> sqlalchemy.RowMapping | None:
        query = (
            sqlalchemy.insert(models.Booking)
            .values(**data)
            .returning(
                models.Booking.id,
                models.Booking.user_id,
                models.Booking.service_id,
                models.Booking.master_id,
                models.Booking.availability_slot_id,
                models.Booking.start_time,
                models.Booking.end_time,
                models.Booking.status,
                models.Booking.comment,
            )
        )
        mark_slot_query = (
            sqlalchemy.update(models.MasterAvailabilitySlot)
            .where(models.MasterAvailabilitySlot.id == data["availability_slot_id"])
            .values(is_booked=True)
        )

        try:
            result = await session.execute(query)
            await session.execute(mark_slot_query)
            await session.commit()
            return result.mappings().first()
        except IntegrityError as e:
            await session.rollback()
            logger.warning("Integrity error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Integrity error")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")

    @staticmethod
    async def select_booking_by_id(
        booking_id: int,
        session: AsyncSession,
    ) -> models.Booking | None:
        query = sqlalchemy.select(models.Booking).where(models.Booking.id == booking_id)
        return await session.scalar(query)

    @staticmethod
    async def update_booking_status(
        booking_id: int,
        status: models.BookingStatus,
        release_slot: bool,
        session: AsyncSession,
    ) -> sqlalchemy.RowMapping | None:
        booking = await BookingRepository.select_booking_by_id(
            booking_id=booking_id, session=session
        )
        if booking is None:
            return None

        query = (
            sqlalchemy.update(models.Booking)
            .where(models.Booking.id == booking_id)
            .values(status=status)
            .returning(
                models.Booking.id,
                models.Booking.user_id,
                models.Booking.service_id,
                models.Booking.master_id,
                models.Booking.availability_slot_id,
                models.Booking.start_time,
                models.Booking.end_time,
                models.Booking.status,
                models.Booking.comment,
            )
        )

        try:
            result = await session.execute(query)
            if release_slot:
                await session.execute(
                    sqlalchemy.update(models.MasterAvailabilitySlot)
                    .where(
                        models.MasterAvailabilitySlot.id == booking.availability_slot_id
                    )
                    .values(is_booked=False)
                )
            await session.commit()
            return result.mappings().first()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")

    @staticmethod
    def bookings_filter(
        query: sqlalchemy.Select,
        data: schemas.ListBookingsRequestSchemas,
        current_user: models.User,
    ) -> sqlalchemy.Select:
        if data.filters and data.filters.status is not None:
            query = query.where(models.Booking.status == data.filters.status)

        if current_user.role == models.RoleType.USER:
            query = query.where(models.Booking.user_id == current_user.id)
        elif current_user.role == models.RoleType.MASTER:
            query = query.where(models.Booking.master_id == current_user.id)

        return query

    @staticmethod
    def bookings_order_by(
        query: sqlalchemy.Select,
        order_by: consts.BookingOrderByType | None,
    ) -> sqlalchemy.Select:
        booking_order = consts.BookingOrderByType
        order_mapping = {
            booking_order.CREATED_AT_ASC: models.Booking.created_at.asc(),
            booking_order.CREATED_AT_DESC: models.Booking.created_at.desc(),
            booking_order.START_TIME_ASC: models.Booking.start_time.asc(),
            booking_order.START_TIME_DESC: models.Booking.start_time.desc(),
        }
        return query.order_by(
            order_mapping.get(order_by, models.Booking.created_at.desc())
        )

    @staticmethod
    async def select_bookings(
        data: schemas.ListBookingsRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> tuple[list[sqlalchemy.RowMapping], int]:
        query = sqlalchemy.select(
            models.Booking.id,
            models.Booking.user_id,
            models.Booking.service_id,
            models.Booking.master_id,
            models.Booking.availability_slot_id,
            models.Booking.start_time,
            models.Booking.end_time,
            models.Booking.status,
            models.Booking.comment,
        )
        query = BookingRepository.bookings_filter(
            query=query, data=data, current_user=current_user
        )

        count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(
            query.subquery()
        )
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        query = BookingRepository.bookings_order_by(query=query, order_by=data.order_by)
        query = query.limit(data.limit).offset(data.offset)

        try:
            result = await session.execute(query)
            return list(result.mappings().all()), total
        except SQLAlchemyError as e:
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")
