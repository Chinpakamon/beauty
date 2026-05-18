import sqlalchemy

from app.api.user import consts
from app.core.security import hash_password
from app.core.database import models
from app.core.settings import settings

async def create_dev_admin(session):
    result = await session.execute(
        sqlalchemy.select(models.User).where(models.User.email == settings.admin_email)
    )
    admin = result.scalar_one_or_none()

    if admin:
        return

    admin = models.User(
        email=settings.admin_email,
        password_hash=hash_password(settings.admin_password),
        role=consts.Role.ADMIN,
        first_name=settings.admin_first_name,
        last_name=settings.admin_last_name,
        phone_number=settings.admin_phone_number,
        is_active=True,
    )

    session.add(admin)
    await session.commit()