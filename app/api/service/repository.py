import logging

import sqlalchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.globals import exceptions as global_exceptions
from app.api.service import consts, schemas
from app.core.database import models

logger = logging.getLogger(__name__)


class ServiceRepository:

    @staticmethod
    async def select_service_by_id(
        service_id: int,
        session: AsyncSession,
    ) -> models.Service | None:
        query = sqlalchemy.select(models.Service).where(models.Service.id == service_id)
        return await session.scalar(query)

    @staticmethod
    async def select_exists_service_by_master_and_type(
        master_id: int,
        service_type_id: int,
        session: AsyncSession,
        exclude_service_id: int | None = None,
    ) -> bool:
        conditions = [
            models.Service.master_id == master_id,
            models.Service.service_type_id == service_type_id,
        ]

        if exclude_service_id is not None:
            conditions.append(models.Service.id != exclude_service_id)

        query = sqlalchemy.select(
            sqlalchemy.exists().where(sqlalchemy.and_(*conditions))
        )
        result = await session.execute(query)
        return result.scalar()

    @staticmethod
    async def insert_service(
        data: dict,
        session: AsyncSession,
    ) -> sqlalchemy.RowMapping | None:
        query = (
            sqlalchemy.insert(models.Service)
            .values(**data)
            .returning(
                models.Service.id,
                models.Service.service_type_id,
                models.Service.master_id,
                models.Service.price,
                models.Service.duration_minutes,
                models.Service.description,
                models.Service.is_active,
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
    async def update_service(
        service_id: int,
        data: dict,
        session: AsyncSession,
    ) -> sqlalchemy.RowMapping | None:
        query = (
            sqlalchemy.update(models.Service)
            .where(models.Service.id == service_id)
            .values(**data)
            .returning(
                models.Service.id,
                models.Service.service_type_id,
                models.Service.master_id,
                models.Service.price,
                models.Service.duration_minutes,
                models.Service.description,
                models.Service.is_active,
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
    def service_list_filter(
        query: sqlalchemy.Select,
        data: schemas.ListServiceRequestSchemas,
    ) -> sqlalchemy.Select:
        if not data.filters:
            return query

        f = data.filters

        if f.master_id is not None:
            query = query.where(models.Service.master_id == f.master_id)

        if f.service_type_id is not None:
            query = query.where(models.Service.service_type_id == f.service_type_id)

        if f.is_active is not None:
            query = query.where(models.Service.is_active.is_(f.is_active))

        if f.min_price is not None:
            query = query.where(models.Service.price >= f.min_price)

        if f.max_price is not None:
            query = query.where(models.Service.price <= f.max_price)

        return query

    @staticmethod
    def service_list_order_by(
        query: sqlalchemy.Select,
        order_by: consts.ServiceOrderByType | None,
    ) -> sqlalchemy.Select:
        order_mapping = {
            consts.ServiceOrderByType.CREATED_AT_ASC: models.Service.created_at.asc(),
            consts.ServiceOrderByType.CREATED_AT_DESC: models.Service.created_at.desc(),
            consts.ServiceOrderByType.PRICE_ASC: models.Service.price.asc(),
            consts.ServiceOrderByType.PRICE_DESC: models.Service.price.desc(),
            consts.ServiceOrderByType.DURATION_ASC: models.Service.duration_minutes.asc(),
            consts.ServiceOrderByType.DURATION_DESC: models.Service.duration_minutes.desc(),
        }

        return query.order_by(
            order_mapping.get(order_by, models.Service.created_at.desc())
        )

    @staticmethod
    async def select_list_service(
        data: schemas.ListServiceRequestSchemas,
        session: AsyncSession,
    ) -> tuple[list[sqlalchemy.RowMapping], int]:
        query = sqlalchemy.select(
            models.Service.id,
            models.Service.service_type_id,
            models.Service.master_id,
            models.Service.price,
            models.Service.duration_minutes,
            models.Service.description,
            models.Service.is_active,
        )

        query = ServiceRepository.service_list_filter(query=query, data=data)

        count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(
            query.subquery()
        )
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        query = ServiceRepository.service_list_order_by(
            query=query, order_by=data.order_by
        )
        query = query.limit(data.limit).offset(data.offset)

        try:
            result = await session.execute(query)
            return result.mappings().all(), total
        except SQLAlchemyError as e:
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")
