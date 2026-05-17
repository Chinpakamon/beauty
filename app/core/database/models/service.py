from sqlalchemy import orm
import sqlalchemy

from app.core import database
from app.core.database import mixins


class Service(database.Base, mixins.PrimaryKeyMixin, mixins.TimestampMixin):
    __tablename__ = "services"

    service_type_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("service_types.id"),
        nullable=False
    )
    master_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("users.id"),
        nullable=False
    )
    price: orm.Mapped[float] = orm.mapped_column(
        sqlalchemy.Float,
        nullable=False
    )
    duration_minutes: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.Integer,
        nullable=False
    )
    description: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String,
        nullable=True
    )
    is_active: orm.Mapped[bool] = orm.mapped_column(
        sqlalchemy.Boolean,
        default=True
    )

    service_type: orm.Mapped["ServiceType"] = orm.relationship(
        back_populates="services"
    )
    master: orm.Mapped["User"] = orm.relationship(
        back_populates="services"
    )
    bookings: orm.Mapped[list["Booking"]] = orm.relationship(
        back_populates="service"
    )
