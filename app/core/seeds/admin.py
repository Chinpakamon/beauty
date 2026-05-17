import sqlalchemy

from app.api.user import consts
from app.core.security import hash_password
from app.core.database import models

async def create_dev_admin(session):
    result = await session.execute(
        sqlalchemy.select(models.User).where(models.User.email == "admin@example.com")
    )
    admin = result.scalar_one_or_none()

    if admin:
        return

    admin = models.User(
        email="admin@example.com",
        password_hash=hash_password("Admin123"),
        role=consts.Role.ADMIN,
        first_name="Admin",
        last_name="Admin",
        phone_number="79991234567",
        is_active=True,
    )

    session.add(admin)
    await session.commit()