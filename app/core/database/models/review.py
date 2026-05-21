import sqlalchemy
from sqlalchemy import orm

from app.core import database
from app.core.database import mixins


class Review(database.Base, mixins.PrimaryKeyMixin, mixins.TimestampMixin):
    __tablename__ = "reviews"

    user_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("users.id"), nullable=False
    )
    service_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("services.id"), nullable=False
    )
    master_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("users.id"), nullable=False
    )
    booking_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("bookings.id"), nullable=False, unique=True
    )
    rating: orm.Mapped[int] = orm.mapped_column(sqlalchemy.Integer, nullable=False)
    text: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, nullable=True)

    booking: orm.Mapped["Booking"] = orm.relationship(back_populates="review")
