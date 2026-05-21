import logging

import sqlalchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.globals import exceptions as global_exceptions
from app.api.service_type import consts, schemas
from app.core.database import models

logger = logging.getLogger(__name__)


class ServiceTypeRepository:

    @staticmethod
    async def select_service_type_by_id(
        service_type_id: int,
        session: AsyncSession,
    ) -> models.ServiceType | None:
        query = sqlalchemy.select(models.ServiceType).where(
            models.ServiceType.id == service_type_id
        )
        return await session.scalar(query)

    @staticmethod
    async def select_exists_service_type_by_name(
        name: str,
        session: AsyncSession,
        exclude_service_type_id: int | None = None,
    ) -> bool:
        query = sqlalchemy.select(
            sqlalchemy.exists().where(
                sqlalchemy.func.lower(models.ServiceType.name) == name.lower()
            )
        )

        if exclude_service_type_id is not None:
            query = sqlalchemy.select(
                sqlalchemy.exists().where(
                    sqlalchemy.and_(
                        sqlalchemy.func.lower(models.ServiceType.name) == name.lower(),
                        models.ServiceType.id != exclude_service_type_id,
                    )
                )
            )

        result = await session.execute(query)
        return result.scalar()

    @staticmethod
    async def insert_service_type(
        data: dict,
        session: AsyncSession,
    ) -> sqlalchemy.RowMapping | None:
        query = (
            sqlalchemy.insert(models.ServiceType)
            .values(**data)
            .returning(
                models.ServiceType.id,
                models.ServiceType.name,
                models.ServiceType.description,
                models.ServiceType.is_active,
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
    async def update_service_type(
        service_type_id: int,
        data: dict,
        session: AsyncSession,
    ) -> sqlalchemy.RowMapping | None:
        query = (
            sqlalchemy.update(models.ServiceType)
            .where(models.ServiceType.id == service_type_id)
            .values(**data)
            .returning(
                models.ServiceType.id,
                models.ServiceType.name,
                models.ServiceType.description,
                models.ServiceType.is_active,
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
    def service_type_list_filter(
        query: sqlalchemy.Select,
        data: schemas.ListServiceTypeRequestSchemas,
    ) -> sqlalchemy.Select:
        if not data.filters:
            return query

        f = data.filters

        if f.name:
            query = query.where(models.ServiceType.name.ilike(f"%{f.name}%"))

        if f.is_active is not None:
            query = query.where(models.ServiceType.is_active.is_(f.is_active))

        return query

    @staticmethod
    def service_type_list_order_by(
        query: sqlalchemy.Select,
        order_by: consts.ServiceTypeOrderByType | None,
    ) -> sqlalchemy.Select:
        order_mapping = {
            consts.ServiceTypeOrderByType.CREATED_AT_ASC: models.ServiceType.created_at.asc(),
            consts.ServiceTypeOrderByType.CREATED_AT_DESC: models.ServiceType.created_at.desc(),
            consts.ServiceTypeOrderByType.NAME_ASC: models.ServiceType.name.asc(),
            consts.ServiceTypeOrderByType.NAME_DESC: models.ServiceType.name.desc(),
        }

        return query.order_by(
            order_mapping.get(order_by, models.ServiceType.created_at.desc())
        )

    @staticmethod
    async def select_list_service_type(
        data: schemas.ListServiceTypeRequestSchemas,
        session: AsyncSession,
    ) -> tuple[list[sqlalchemy.RowMapping], int]:
        query = sqlalchemy.select(
            models.ServiceType.id,
            models.ServiceType.name,
            models.ServiceType.description,
            models.ServiceType.is_active,
        )

        query = ServiceTypeRepository.service_type_list_filter(query=query, data=data)

        count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(
            query.subquery()
        )
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        query = ServiceTypeRepository.service_type_list_order_by(
            query=query,
            order_by=data.order_by,
        )
        query = query.limit(data.limit).offset(data.offset)

        try:
            result = await session.execute(query)
            return result.mappings().all(), total
        except SQLAlchemyError as e:
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")
