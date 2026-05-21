import pydantic

from app.api.user import consts
from app.core import validators


class RegistrationUserRequestSchemas(pydantic.BaseModel):
    email: pydantic.EmailStr
    password: str
    first_name: str
    last_name: str | None = None
    role: consts.RegistrationRole = consts.RegistrationRole.USER
    phone_number: str

    @pydantic.field_validator("phone_number")
    @classmethod
    def validate_phone_number_field(cls, value: str | None) -> str | None:
        return validators.validate_phone_number(value)

    @pydantic.field_validator("password")
    @classmethod
    def validate_password_field(cls, value: str) -> str:
        return validators.validate_password(value)


class RegistrationUserResponseSchemas(pydantic.BaseModel):
    id: int
    email: pydantic.EmailStr
    access_token: str

    model_config = pydantic.ConfigDict(from_attributes=True)


class LoginUserRequestSchemas(pydantic.BaseModel):
    email: pydantic.EmailStr
    password: str


class LoginUserResponseSchemas(pydantic.BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponseSchemas(pydantic.BaseModel):
    id: int
    email: pydantic.EmailStr
    first_name: str
    last_name: str | None
    role: str
    phone_number: str


class UserMeResponseSchemas(UserResponseSchemas): ...


class GetUserResponseSchemas(UserResponseSchemas):
    model_config = pydantic.ConfigDict(from_attributes=True)


class UpdateUserRequestSchemas(pydantic.BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None

    @pydantic.field_validator("phone_number")
    @classmethod
    def validate_phone_number_field(cls, value: str | None) -> str | None:
        return validators.validate_phone_number(value)


class UpdateUserResponseSchemas(UserResponseSchemas): ...


class DeleteUserResponseSchemas(pydantic.BaseModel):
    success: bool


class ListUserFilters(pydantic.BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: consts.Role | None = None
    phone_number: str | None = None
    email: pydantic.EmailStr | None = None


class ListUserRequestSchemas(pydantic.BaseModel):
    filters: ListUserFilters | None = None
    order_by: consts.UserOrderByType | None = consts.UserOrderByType.CREATED_AT_DESC
    limit: int | None = 10
    offset: int | None = 0


class ListUserItemResponseSchemas(UserResponseSchemas): ...


class ListUserResponseSchemas(pydantic.BaseModel):
    data: list[ListUserItemResponseSchemas]
    total: int
    limit: int
    offset: int


class UpdateUserPasswordRequestSchemas(pydantic.BaseModel):
    old_password: str
    new_password: str

    @pydantic.field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validators.validate_password(value)


class UpdateUserPasswordResponseSchemas(pydantic.BaseModel):
    success: bool


class UpdateUserEmailRequestSchemas(pydantic.BaseModel):
    new_email: pydantic.EmailStr
    password: str


class UpdateUserEmailResponseSchemas(pydantic.BaseModel):
    success: bool


class UpdateUserRoleRequestSchemas(pydantic.BaseModel):
    user_id: int
    new_role: consts.Role


class UpdateUserRoleResponseSchemas(pydantic.BaseModel):
    success: bool
