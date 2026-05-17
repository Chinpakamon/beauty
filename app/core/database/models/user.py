import enum

from sqlalchemy import orm
import sqlalchemy

from app.core import database
from app.core.database import mixins


class RoleType(enum.Enum):
    USER = "USER"
    MASTER = "MASTER"
    ADMIN = "ADMIN"


class User(database.Base, mixins.PrimaryKeyMixin, mixins.TimestampMixin):
    __tablename__ = "users"

    email: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String,
        nullable=False,
        unique=True
    )
    password_hash: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String,
        nullable=False
    )
    role: orm.Mapped[RoleType] = orm.mapped_column(
        sqlalchemy.Enum(RoleType),
        nullable=False,
        default=RoleType.USER
    )
    first_name: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String,
        nullable=False
    )
    last_name: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String,
        nullable=True
    )
    phone_number: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String,
        nullable=False
    )
    is_active: orm.Mapped[bool] = orm.mapped_column(
        sqlalchemy.Boolean,
        default=True
    )

    # relationships
    services: orm.Mapped[list["Service"]] = orm.relationship(
        back_populates="master",
        cascade="all, delete-orphan"
    )

    bookings: orm.Mapped[list["Booking"]] = orm.relationship(
        back_populates="user",
        foreign_keys="Booking.user_id"
    )
