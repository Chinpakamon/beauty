import sqlalchemy
from sqlalchemy import orm


class PrimaryKeyMixin:
    id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.BigInteger,
        nullable=False,
        primary_key=True,
        server_default=sqlalchemy.Identity(start=1, always=True),
    )
