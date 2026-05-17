import typing

import sqlalchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.globals import exceptions as global_exceptions
from app.api.user import consts, schemas
from app.core.database import models

import logging

logger = logging.getLogger(__name__)


class UserRepository:

    @staticmethod
    async def select_exists_user_by_email(email: str, session: AsyncSession,) -> bool:
        query = sqlalchemy.select(sqlalchemy.exists().where(
            sqlalchemy.and_(models.User.email == email, models.User.is_active.is_(True))
            )
        )
        result = await session.execute(query)
        return result.scalar()


    @staticmethod
    async def insert_user(data: dict, session: AsyncSession) -> sqlalchemy.RowMapping | None:
        query = (
            sqlalchemy.insert(models.User)
            .values(**data)
            .returning(
                models.User.id,
                models.User.email,
                models.User.role
            )
        )

        try:
            result = await session.execute(query)
            await session.commit()
            return result.mappings().first()
        except IntegrityError as e:
            await session.rollback()
            logger.warning("Integrity error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Integrity error")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")


    @staticmethod
    async def select_user_by_email(
        email: str, session: AsyncSession
    ) -> models.User | None:
        query = sqlalchemy.select(models.User).where(
            sqlalchemy.and_(models.User.email == email, models.User.is_active.is_(True))
        )
        return await session.scalar(query)


    @staticmethod
    async def select_user_by_id(
        user_id: int, session: AsyncSession
    ) -> models.User | None:
        query = sqlalchemy.select(models.User).where(
            sqlalchemy.and_(models.User.id == user_id, models.User.is_active.is_(True))
        )
        return await session.scalar(query)


    @staticmethod
    async def update_user(user_id: int, data: dict, session: AsyncSession) -> sqlalchemy.RowMapping | None:
        query = (
            sqlalchemy.update(models.User)
            .where(sqlalchemy.and_(models.User.id == user_id, models.User.is_active.is_(True)))
            .values(**data)
            .returning(
                models.User.id,
                models.User.email,
                models.User.first_name,
                models.User.last_name,
                models.User.role,
                models.User.phone_number
            )
        )

        try:
            result = await session.execute(query)
            await session.commit()
            return result.mappings().first()
        except IntegrityError as e:
            await session.rollback()
            logger.warning("Integrity error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Integrity error")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")


    @staticmethod
    async def delete_user(user_id: int, session: AsyncSession) -> None:
        query = (
            sqlalchemy.update(models.User)
            .where(sqlalchemy.and_(models.User.id == user_id, models.User.is_active.is_(True)))
            .values(is_active=False)
        )

        try:
            await session.execute(query)
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            logger.warning("Integrity error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Integrity error")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")


    @staticmethod
    def user_list_filter(
        query: sqlalchemy.Select,
        data: schemas.ListUserRequestSchemas,
    ) -> sqlalchemy.Select:

        if not data.filters:
            return query

        f = data.filters

        if f.first_name:
            query = query.where(models.User.first_name == f.first_name)

        if f.last_name:
            query = query.where(models.User.last_name == f.last_name)

        if f.email:
            query = query.where(models.User.email == f.email)

        if f.phone_number:
            query = query.where(models.User.phone_number == f.phone_number)

        if f.role:
            query = query.where(models.User.role == f.role)

        return query
    

    @staticmethod
    def user_list_order_by(
        query: sqlalchemy.Select,
        order_by: consts.UserOrderByType | None,
    ) -> sqlalchemy.Select:

        order_mapping = {
            consts.UserOrderByType.CREATED_AT_ASC: models.User.created_at.asc(),
            consts.UserOrderByType.CREATED_AT_DESC: models.User.created_at.desc(),
            consts.UserOrderByType.FIRST_NAME_ASC: models.User.first_name.asc(),
            consts.UserOrderByType.FIRST_NAME_DESC: models.User.first_name.desc(),
            consts.UserOrderByType.LAST_NAME_ASC: models.User.last_name.asc(),
            consts.UserOrderByType.LAST_NAME_DESC: models.User.last_name.desc(),
            consts.UserOrderByType.EMAIL_ASC: models.User.email.asc(),
            consts.UserOrderByType.EMAIL_DESC: models.User.email.desc(),
        }

        return query.order_by(
            order_mapping.get(order_by, models.User.created_at.desc())
        )


    @staticmethod
    async def select_list_user(
        data: schemas.ListUserRequestSchemas,
        session: AsyncSession
    ) -> tuple[typing.Sequence[sqlalchemy.RowMapping], int]:

        query = (
            sqlalchemy.select(
                models.User.id,
                models.User.email,
                models.User.first_name,
                models.User.last_name,
                models.User.role,
                models.User.phone_number
            )
            .where(models.User.is_active.is_(True))
        )

        query = UserRepository.user_list_filter(query=query, data=data)

        count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        query = UserRepository.user_list_order_by(query=query, order_by=data.order_by)

        query = query.limit(data.limit).offset(data.offset)

        try:
            result = await session.execute(query)
            return result.mappings().all(), total
        except SQLAlchemyError as e:
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")


    @staticmethod
    async def update_password(
        user: models.User,
        new_password_hash: str,
        session: AsyncSession
    ) -> None:
        query = (
            sqlalchemy.update(models.User)
            .where(sqlalchemy.and_(models.User.id == user.id, models.User.is_active.is_(True)))
            .values(password_hash=new_password_hash)
        )

        try:
            await session.execute(query)
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            logger.warning("Integrity error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Integrity error")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")


    @staticmethod
    async def update_email(
        user: models.User,
        new_email: str,
        session: AsyncSession
    ) -> None:
        query = (
            sqlalchemy.update(models.User)
            .where(sqlalchemy.and_(models.User.id == user.id, models.User.is_active.is_(True)))
            .values(email=new_email)
        )

        try:
            await session.execute(query)
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            logger.warning("Integrity error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Integrity error")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")


    @staticmethod
    async def update_role(
        user_id: int,
        new_role: str,
        session: AsyncSession
    ) -> None:
        query = (
            sqlalchemy.update(models.User)
            .where(sqlalchemy.and_(models.User.id == user_id, models.User.is_active.is_(True)))
            .values(role=new_role)
        )

        try:
            await session.execute(query)
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            logger.warning("Integrity error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Integrity error")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")
