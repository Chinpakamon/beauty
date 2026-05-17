import datetime

from sqlalchemy import DateTime, func, orm


class TimestampMixin:
    created_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        DateTime, default=func.now(), nullable=False
    )
