import datetime

import sqlalchemy
from sqlalchemy import orm

from app.core import database
from app.core.database import mixins


class MasterAvailabilitySlot(
    database.Base, mixins.PrimaryKeyMixin, mixins.TimestampMixin
):
    __tablename__ = "master_availability_slots"
    __table_args__ = (
        sqlalchemy.UniqueConstraint(
            "master_id",
            "start_time",
            name="uq_master_availability_slots_master_id_start_time",
        ),
    )

    master_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("users.id"), nullable=False
    )
    start_time: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sqlalchemy.DateTime, nullable=False
    )
    end_time: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sqlalchemy.DateTime, nullable=False
    )
    is_booked: orm.Mapped[bool] = orm.mapped_column(
        sqlalchemy.Boolean, nullable=False, default=False
    )

    master: orm.Mapped["User"] = orm.relationship(
        back_populates="availability_slots", foreign_keys=[master_id]
    )
    booking: orm.Mapped["Booking"] = orm.relationship(
        back_populates="availability_slot", uselist=False
    )
