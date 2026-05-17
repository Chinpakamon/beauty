from sqlalchemy import orm
import sqlalchemy

from app.core import database
from app.core.database import mixins


class ServiceType(database.Base, mixins.PrimaryKeyMixin, mixins.TimestampMixin):
    __tablename__ = "service_types"

    name: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String,
        nullable=False,
        unique=True
    )
    description: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String,
        nullable=True
    )
    is_active: orm.Mapped[bool] = orm.mapped_column(
        sqlalchemy.Boolean,
        default=True
    )

    services: orm.Mapped[list["Service"]] = orm.relationship(
        back_populates="service_type"
    )
