import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import models


class GloablUserRepository:

    @staticmethod
    async def select_user_by_id(
        user_id: int, session: AsyncSession
    ) -> models.User | None:
        query = sqlalchemy.select(models.User).where(models.User.id == user_id)
        return await session.scalar(query)
