import datetime

import pydantic

from app.api.review import consts


class ReviewBaseResponseSchemas(pydantic.BaseModel):
    id: int
    user_id: int
    service_id: int
    master_id: int
    booking_id: int
    rating: int
    text: str | None
    created_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)


class CreateReviewRequestSchemas(pydantic.BaseModel):
    booking_id: int
    rating: int = pydantic.Field(ge=1, le=5)
    text: str | None = pydantic.Field(default=None, max_length=2000)


class CreateReviewResponseSchemas(ReviewBaseResponseSchemas): ...


class GetReviewResponseSchemas(ReviewBaseResponseSchemas): ...


class UpdateReviewRequestSchemas(pydantic.BaseModel):
    rating: int | None = pydantic.Field(default=None, ge=1, le=5)
    text: str | None = pydantic.Field(default=None, max_length=2000)

    @pydantic.model_validator(mode="after")
    def validate_rating_is_not_null(self):
        if "rating" in self.model_fields_set and self.rating is None:
            raise ValueError("rating cannot be null")
        return self


class UpdateReviewResponseSchemas(ReviewBaseResponseSchemas): ...


class DeleteReviewResponseSchemas(pydantic.BaseModel):
    detail: str


class ListReviewsFilters(pydantic.BaseModel):
    service_id: int | None = None
    master_id: int | None = None
    user_id: int | None = None
    rating: int | None = pydantic.Field(default=None, ge=1, le=5)


class ListReviewsRequestSchemas(pydantic.BaseModel):
    filters: ListReviewsFilters | None = None
    order_by: consts.ReviewOrderByType | None = consts.ReviewOrderByType.CREATED_AT_DESC
    limit: int = pydantic.Field(default=10, ge=1, le=100)
    offset: int = pydantic.Field(default=0, ge=0)


class ListReviewsResponseSchemas(pydantic.BaseModel):
    data: list[ReviewBaseResponseSchemas]
    total: int
    limit: int
    offset: int
