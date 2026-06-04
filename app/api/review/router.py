from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.review import schemas, service
from app.core.database.core import get_session
from app.core.middleware import dependencies

router = APIRouter(prefix="/review", tags=["Review"])


@router.post("/create", response_model=schemas.CreateReviewResponseSchemas)
async def create_review(
    data: schemas.CreateReviewRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.get_current_user_dep),
):
    return await service.ReviewService.create_review(
        data=data,
        current_user=current_user,
        session=session,
    )


@router.get("/{review_id:int}", response_model=schemas.GetReviewResponseSchemas)
async def get_review(
    review_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await service.ReviewService.get_review(
        review_id=review_id,
        session=session,
    )


@router.get("/list", response_model=schemas.ListReviewsResponseSchemas)
async def review_list(
    data: schemas.ListReviewsRequestSchemas = Body(
        default=schemas.ListReviewsRequestSchemas()
    ),
    session: AsyncSession = Depends(get_session),
):
    return await service.ReviewService.get_review_list(data=data, session=session)


@router.patch("/{review_id:int}", response_model=schemas.UpdateReviewResponseSchemas)
async def update_review(
    review_id: int,
    data: schemas.UpdateReviewRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.get_current_user_dep),
):
    return await service.ReviewService.update_review(
        review_id=review_id,
        data=data,
        current_user=current_user,
        session=session,
    )


@router.delete("/{review_id:int}", response_model=schemas.DeleteReviewResponseSchemas)
async def delete_review(
    review_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_admin),
):
    return await service.ReviewService.delete_review(
        review_id=review_id,
        session=session,
    )
