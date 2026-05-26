import sqlalchemy
from sqlalchemy import orm


class PrimaryKeyMixin:
    id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.BigInteger().with_variant(sqlalchemy.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
