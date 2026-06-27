from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.user import schemas, service
from app.core.database.core import get_session
from app.core.middleware import dependencies

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/registration", response_model=schemas.RegistrationUserResponseSchemas)
async def user_registration(
    data: schemas.RegistrationUserRequestSchemas,
    session: AsyncSession = Depends(get_session),
):
    return await service.UserService.registration_user(data=data, session=session)


@router.post("/login", response_model=schemas.LoginUserResponseSchemas)
async def login(
    data: schemas.LoginUserRequestSchemas, session: AsyncSession = Depends(get_session)
):
    return await service.UserService.login(data=data, session=session)


@router.get("/me", response_model=schemas.UserMeResponseSchemas)
async def me(user=Depends(dependencies.get_current_user_dep)):
    return schemas.UserMeResponseSchemas(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        phone_number=user.phone_number,
    )


@router.get("/{user_id:int}", response_model=schemas.GetUserResponseSchemas)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    user=Depends(dependencies.get_current_user_dep),
):
    return await service.UserService.get_user(user_id=user_id, session=session)


@router.post("/update/{user_id}", response_model=schemas.UpdateUserResponseSchemas)
async def user_update(
    user_id: int,
    data: schemas.UpdateUserRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.get_current_user_dep),
):
    return await service.UserService.update_user(
        data=data,
        user_id=user_id,
        session=session,
        current_user=current_user,
    )


@router.post("/delete/{user_id}", response_model=schemas.DeleteUserResponseSchemas)
async def user_delete(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.get_current_user_dep),
):
    return await service.UserService.delete_user(
        user_id=user_id, session=session, current_user=current_user
    )


@router.get("/list", response_model=schemas.ListUserResponseSchemas)
@router.post("/list", response_model=schemas.ListUserResponseSchemas)
async def user_list(
    data: schemas.ListUserRequestSchemas = Body(),
    session: AsyncSession = Depends(get_session),
):
    return await service.UserService.get_user_list(data=data, session=session)


@router.patch(
    "/change-password", response_model=schemas.UpdateUserPasswordResponseSchemas
)
async def change_password(
    data: schemas.UpdateUserPasswordRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.get_current_user_dep),
):
    return await service.UserService.change_password(
        data=data,
        session=session,
        current_user=current_user,
    )


@router.patch("/change-email", response_model=schemas.UpdateUserEmailResponseSchemas)
async def change_email(
    data: schemas.UpdateUserEmailRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.get_current_user_dep),
):
    return await service.UserService.change_email(
        data=data,
        session=session,
        current_user=current_user,
    )


@router.patch("/change-role", response_model=schemas.UpdateUserRoleResponseSchemas)
async def change_role(
    data: schemas.UpdateUserRoleRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_admin),
):
    return await service.UserService.change_role(
        data=data,
        session=session,
        current_user=current_user,
    )
