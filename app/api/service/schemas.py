import pydantic

from app.api.service import consts


class ServiceBaseResponseSchemas(pydantic.BaseModel):
    id: int
    service_type_id: int
    master_id: int
    price: float
    duration_minutes: int
    description: str | None
    is_active: bool

    model_config = pydantic.ConfigDict(from_attributes=True)


class CreateServiceRequestSchemas(pydantic.BaseModel):
    service_type_id: int
    price: float = pydantic.Field(gt=0)
    duration_minutes: int = pydantic.Field(gt=0, le=24 * 60)
    description: str | None = pydantic.Field(default=None, max_length=1000)
    master_id: int | None = None


class CreateServiceResponseSchemas(ServiceBaseResponseSchemas): ...


class GetServiceResponseSchemas(ServiceBaseResponseSchemas): ...


class UpdateServiceRequestSchemas(pydantic.BaseModel):
    service_type_id: int | None = None
    price: float | None = pydantic.Field(default=None, gt=0)
    duration_minutes: int | None = pydantic.Field(default=None, gt=0, le=24 * 60)
    description: str | None = pydantic.Field(default=None, max_length=1000)
    master_id: int | None = None


class UpdateServiceResponseSchemas(ServiceBaseResponseSchemas): ...


class ChangeServiceStatusRequestSchemas(pydantic.BaseModel):
    is_active: bool


class ChangeServiceStatusResponseSchemas(ServiceBaseResponseSchemas): ...


class DeleteServiceResponseSchemas(pydantic.BaseModel):
    success: bool


class ListServiceFilters(pydantic.BaseModel):
    master_id: int | None = None
    service_type_id: int | None = None
    is_active: bool | None = None
    min_price: float | None = pydantic.Field(default=None, ge=0)
    max_price: float | None = pydantic.Field(default=None, ge=0)


class ListServiceRequestSchemas(pydantic.BaseModel):
    filters: ListServiceFilters | None = None
    order_by: consts.ServiceOrderByType | None = consts.ServiceOrderByType.CREATED_AT_DESC
    limit: int = pydantic.Field(default=10, ge=1, le=100)
    offset: int = pydantic.Field(default=0, ge=0)


class ListServiceItemResponseSchemas(ServiceBaseResponseSchemas): ...


class ListServiceResponseSchemas(pydantic.BaseModel):
    data: list[ListServiceItemResponseSchemas]
    total: int
    limit: int
    offset: int
