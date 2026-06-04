import logging

import sqlalchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.globals import exceptions as global_exceptions
from app.api.review import consts, schemas
from app.core.database import models

logger = logging.getLogger(__name__)


REVIEW_COLUMNS = (
    models.Review.id,
    models.Review.user_id,
    models.Review.service_id,
    models.Review.master_id,
    models.Review.booking_id,
    models.Review.rating,
    models.Review.text,
    models.Review.created_at,
)


class ReviewRepository:
    @staticmethod
    async def insert_review(
        data: dict,
        session: AsyncSession,
    ) -> sqlalchemy.RowMapping | None:
        query = (
            sqlalchemy.insert(models.Review)
            .values(**data)
            .returning(*REVIEW_COLUMNS)
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
    async def select_review_by_id(
        review_id: int,
        session: AsyncSession,
    ) -> models.Review | None:
        query = sqlalchemy.select(models.Review).where(models.Review.id == review_id)
        return await session.scalar(query)

    @staticmethod
    async def select_review_by_booking_id(
        booking_id: int,
        session: AsyncSession,
    ) -> models.Review | None:
        query = sqlalchemy.select(models.Review).where(
            models.Review.booking_id == booking_id
        )
        return await session.scalar(query)

    @staticmethod
    async def update_review(
        review_id: int,
        data: dict,
        session: AsyncSession,
    ) -> sqlalchemy.RowMapping | None:
        query = (
            sqlalchemy.update(models.Review)
            .where(models.Review.id == review_id)
            .values(**data)
            .returning(*REVIEW_COLUMNS)
        )

        try:
            result = await session.execute(query)
            await session.commit()
            return result.mappings().first()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")

    @staticmethod
    async def delete_review(
        review_id: int,
        session: AsyncSession,
    ) -> bool:
        query = sqlalchemy.delete(models.Review).where(models.Review.id == review_id)

        try:
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")

    @staticmethod
    def reviews_filter(
        query: sqlalchemy.Select,
        data: schemas.ListReviewsRequestSchemas,
    ) -> sqlalchemy.Select:
        if data.filters is None:
            return query

        if data.filters.service_id is not None:
            query = query.where(models.Review.service_id == data.filters.service_id)
        if data.filters.master_id is not None:
            query = query.where(models.Review.master_id == data.filters.master_id)
        if data.filters.user_id is not None:
            query = query.where(models.Review.user_id == data.filters.user_id)
        if data.filters.rating is not None:
            query = query.where(models.Review.rating == data.filters.rating)

        return query

    @staticmethod
    def reviews_order_by(
        query: sqlalchemy.Select,
        order_by: consts.ReviewOrderByType | None,
    ) -> sqlalchemy.Select:
        review_order = consts.ReviewOrderByType
        order_mapping = {
            review_order.CREATED_AT_ASC: models.Review.created_at.asc(),
            review_order.CREATED_AT_DESC: models.Review.created_at.desc(),
            review_order.RATING_ASC: models.Review.rating.asc(),
            review_order.RATING_DESC: models.Review.rating.desc(),
        }
        return query.order_by(
            order_mapping.get(order_by, models.Review.created_at.desc())
        )

    @staticmethod
    async def select_reviews(
        data: schemas.ListReviewsRequestSchemas,
        session: AsyncSession,
    ) -> tuple[list[sqlalchemy.RowMapping], int]:
        query = sqlalchemy.select(*REVIEW_COLUMNS)
        query = ReviewRepository.reviews_filter(query=query, data=data)

        count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(
            query.subquery()
        )
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        query = ReviewRepository.reviews_order_by(query=query, order_by=data.order_by)
        query = query.limit(data.limit).offset(data.offset)

        try:
            result = await session.execute(query)
            return list(result.mappings().all()), total
        except SQLAlchemyError as e:
            logger.error("Database error occurred", exc_info=e)
            raise global_exceptions.DatabaseException("Database error")
