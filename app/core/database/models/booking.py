import datetime
import enum

import sqlalchemy
from sqlalchemy import orm

from app.core import database
from app.core.database import mixins


class BookingStatus(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class Booking(database.Base, mixins.PrimaryKeyMixin, mixins.TimestampMixin):
    __tablename__ = "bookings"

    user_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("users.id"), nullable=False
    )
    service_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("services.id"), nullable=False
    )
    master_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("users.id"), nullable=False
    )
    availability_slot_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("master_availability_slots.id"),
        nullable=False,
    )
    start_time: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sqlalchemy.DateTime, nullable=False
    )
    end_time: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sqlalchemy.DateTime, nullable=False
    )
    status: orm.Mapped[BookingStatus] = orm.mapped_column(
        sqlalchemy.Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False
    )
    comment: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, nullable=True)

    user: orm.Mapped["User"] = orm.relationship(
        back_populates="bookings", foreign_keys=[user_id]
    )
    service: orm.Mapped["Service"] = orm.relationship(back_populates="bookings")
    master: orm.Mapped["User"] = orm.relationship(foreign_keys=[master_id])
    availability_slot: orm.Mapped["MasterAvailabilitySlot"] = orm.relationship(
        back_populates="booking"
    )
    review: orm.Mapped["Review"] = orm.relationship(
        back_populates="booking", uselist=False
    )
