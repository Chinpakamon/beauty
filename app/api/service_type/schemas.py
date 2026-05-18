import pydantic

from app.api.service_type import consts


class ServiceTypeBaseResponseSchemas(pydantic.BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool

    model_config = pydantic.ConfigDict(from_attributes=True)


class CreateServiceTypeRequestSchemas(pydantic.BaseModel):
    name: str = pydantic.Field(min_length=2, max_length=255)
    description: str | None = pydantic.Field(default=None, max_length=1000)


class CreateServiceTypeResponseSchemas(ServiceTypeBaseResponseSchemas): ...


class GetServiceTypeResponseSchemas(ServiceTypeBaseResponseSchemas): ...


class UpdateServiceTypeRequestSchemas(pydantic.BaseModel):
    name: str | None = pydantic.Field(default=None, min_length=2, max_length=255)
    description: str | None = pydantic.Field(default=None, max_length=1000)


class UpdateServiceTypeResponseSchemas(ServiceTypeBaseResponseSchemas): ...


class ChangeServiceTypeStatusRequestSchemas(pydantic.BaseModel):
    is_active: bool


class ChangeServiceTypeStatusResponseSchemas(ServiceTypeBaseResponseSchemas): ...


class ListServiceTypeFilters(pydantic.BaseModel):
    name: str | None = None
    is_active: bool | None = None


class ListServiceTypeRequestSchemas(pydantic.BaseModel):
    filters: ListServiceTypeFilters | None = None
    order_by: consts.ServiceTypeOrderByType | None = (
        consts.ServiceTypeOrderByType.CREATED_AT_DESC
    )
    limit: int = pydantic.Field(default=10, ge=1, le=100)
    offset: int = pydantic.Field(default=0, ge=0)


class ListServiceTypeItemResponseSchemas(ServiceTypeBaseResponseSchemas): ...


class ListServiceTypeResponseSchemas(pydantic.BaseModel):
    data: list[ListServiceTypeItemResponseSchemas]
    total: int
    limit: int
    offset: int
