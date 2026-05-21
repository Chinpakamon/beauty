import sqlalchemy
from sqlalchemy import orm

from app.core import database
from app.core.database import mixins


class Service(database.Base, mixins.PrimaryKeyMixin, mixins.TimestampMixin):
    __tablename__ = "services"
    __table_args__ = (
        sqlalchemy.UniqueConstraint(
            "master_id",
            "service_type_id",
            name="uq_services_master_id_service_type_id",
        ),
    )

    service_type_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("service_types.id"), nullable=False
    )
    master_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("users.id"), nullable=False
    )
    price: orm.Mapped[float] = orm.mapped_column(sqlalchemy.Float, nullable=False)
    duration_minutes: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    description: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, nullable=True)
    is_active: orm.Mapped[bool] = orm.mapped_column(sqlalchemy.Boolean, default=True)

    service_type: orm.Mapped["ServiceType"] = orm.relationship(
        back_populates="services"
    )
    master: orm.Mapped["User"] = orm.relationship(back_populates="services")
    bookings: orm.Mapped[list["Booking"]] = orm.relationship(back_populates="service")
