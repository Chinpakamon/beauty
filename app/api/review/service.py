from sqlalchemy.ext.asyncio import AsyncSession

from app.api.booking import exceptions as booking_exceptions
from app.api.booking import repository as booking_repository
from app.api.review import exceptions, repository, schemas
from app.api.user import exceptions as user_exceptions
from app.core.database import models


class ReviewService:
    @staticmethod
    async def _get_review_or_raise(
        review_id: int,
        session: AsyncSession,
    ) -> models.Review:
        review = await repository.ReviewRepository.select_review_by_id(
            review_id=review_id,
            session=session,
        )
        if not review:
            raise exceptions.ReviewNotFoundException()
        return review

    @staticmethod
    def _ensure_review_owner(
        current_user: models.User,
        review: models.Review,
    ) -> None:
        if current_user.id == review.user_id:
            return
        raise user_exceptions.PermissionDeniedException()

    @staticmethod
    def _ensure_review_owner_or_admin(
        current_user: models.User,
        review: models.Review,
    ) -> None:
        if (
            current_user.id == review.user_id
            or current_user.role == models.RoleType.ADMIN
        ):
            return
        raise user_exceptions.PermissionDeniedException()

    @staticmethod
    async def create_review(
        data: schemas.CreateReviewRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.CreateReviewResponseSchemas:
        booking = await booking_repository.BookingRepository.select_booking_by_id(
            booking_id=data.booking_id,
            session=session,
        )
        if not booking:
            raise booking_exceptions.BookingNotFoundException()

        if booking.user_id != current_user.id:
            raise user_exceptions.PermissionDeniedException()
        if booking.status != models.BookingStatus.COMPLETED:
            raise exceptions.ReviewBookingNotCompletedException()

        existing_review = await repository.ReviewRepository.select_review_by_booking_id(
            booking_id=booking.id,
            session=session,
        )
        if existing_review:
            raise exceptions.ReviewAlreadyExistsException()

        review = await repository.ReviewRepository.insert_review(
            data={
                "user_id": current_user.id,
                "service_id": booking.service_id,
                "master_id": booking.master_id,
                "booking_id": booking.id,
                "rating": data.rating,
                "text": data.text,
            },
            session=session,
        )
        return schemas.CreateReviewResponseSchemas(**review)

    @staticmethod
    async def get_review(
        review_id: int,
        session: AsyncSession,
    ) -> schemas.GetReviewResponseSchemas:
        review = await ReviewService._get_review_or_raise(
            review_id=review_id,
            session=session,
        )
        return schemas.GetReviewResponseSchemas.model_validate(review)

    @staticmethod
    async def update_review(
        review_id: int,
        data: schemas.UpdateReviewRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.UpdateReviewResponseSchemas:
        review = await ReviewService._get_review_or_raise(
            review_id=review_id,
            session=session,
        )
        ReviewService._ensure_review_owner(current_user=current_user, review=review)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return schemas.UpdateReviewResponseSchemas.model_validate(review)

        updated_review = await repository.ReviewRepository.update_review(
            review_id=review_id,
            data=update_data,
            session=session,
        )
        return schemas.UpdateReviewResponseSchemas(**updated_review)

    @staticmethod
    async def delete_review(
        review_id: int,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.DeleteReviewResponseSchemas:
        review = await ReviewService._get_review_or_raise(
            review_id=review_id,
            session=session,
        )
        ReviewService._ensure_review_owner_or_admin(
            current_user=current_user,
            review=review,
        )
        await repository.ReviewRepository.delete_review(
            review_id=review.id,
            session=session,
        )
        return schemas.DeleteReviewResponseSchemas(detail="Review deleted")

    @staticmethod
    async def get_review_list(
        data: schemas.ListReviewsRequestSchemas,
        session: AsyncSession,
    ) -> schemas.ListReviewsResponseSchemas:
        reviews, total = await repository.ReviewRepository.select_reviews(
            data=data,
            session=session,
        )
        return schemas.ListReviewsResponseSchemas(
            data=[schemas.ReviewBaseResponseSchemas(**review) for review in reviews],
            total=total,
            limit=data.limit,
            offset=data.offset,
        )
