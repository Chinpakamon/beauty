import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.globals import exceptions as global_exceptions
from app.api.user import exceptions, repository, schemas
from app.core import security
from app.core.database import models
from app.core.database.models.user import RoleType


class UserService:

    @staticmethod
    async def _get_active_user_or_raise(
        user_id: int, session: AsyncSession
    ) -> models.User:
        user = await repository.UserRepository.select_user_by_id(
            user_id=user_id, session=session
        )
        if not user:
            raise global_exceptions.UserNotFoundException()
        return user

    @staticmethod
    async def registration_user(
        data: schemas.RegistrationUserRequestSchemas, session: AsyncSession
    ) -> schemas.RegistrationUserResponseSchemas:
        existing = await repository.UserRepository.select_exists_user_by_email(
            email=data.email, session=session
        )
        if existing:
            raise exceptions.UserAlreadyExistsException()

        user_data = {
            "email": data.email,
            "password_hash": security.hash_password(data.password),
            "first_name": data.first_name,
            "last_name": data.last_name,
            "role": data.role,
            "phone_number": data.phone_number,
        }

        user = await repository.UserRepository.insert_user(
            data=user_data, session=session
        )
        token = security.create_access_token(
            data={"user_id": str(user.id), "role": user.role.value, "email": user.email}
        )
        return schemas.RegistrationUserResponseSchemas(
            id=user["id"],
            email=user["email"],
            access_token=token,
        )

    @staticmethod
    async def login(
        data: schemas.LoginUserRequestSchemas, session: AsyncSession
    ) -> schemas.LoginUserResponseSchemas:
        user = await repository.UserRepository.select_user_by_email(
            email=data.email,
            session=session,
        )

        if not user or not security.verify_password(
            plain=data.password, hashed=user.password_hash
        ):
            raise exceptions.InvalidCredentialsException()

        token = security.create_access_token(
            data={"user_id": str(user.id), "role": user.role.value, "email": user.email}
        )

        return schemas.LoginUserResponseSchemas(access_token=token)

    @staticmethod
    async def get_user(
        user_id: int, session: AsyncSession
    ) -> schemas.GetUserResponseSchemas:

        user = await UserService._get_active_user_or_raise(
            user_id=user_id, session=session
        )

        return schemas.GetUserResponseSchemas.model_validate(user)

    @staticmethod
    def has_permissions(current_user: models.User, target_user_id: int) -> bool:
        if current_user.role == RoleType.ADMIN:
            return True
        return current_user.id == target_user_id

    @staticmethod
    async def update_user(
        user_id: int,
        current_user: models.User,
        data: schemas.UpdateUserRequestSchemas,
        session: AsyncSession,
    ) -> schemas.UpdateUserResponseSchemas:

        user = await UserService._get_active_user_or_raise(
            user_id=user_id, session=session
        )

        if not UserService.has_permissions(
            current_user=current_user, target_user_id=user.id
        ):
            raise exceptions.PermissionDeniedException()

        updated_user = await repository.UserRepository.update_user(
            data=data.model_dump(exclude_unset=True), session=session, user_id=user_id
        )

        return schemas.UpdateUserResponseSchemas.model_validate(updated_user)

    @staticmethod
    async def delete_user(
        user_id: int, current_user: models.User, session: AsyncSession
    ) -> schemas.DeleteUserResponseSchemas:

        user = await UserService._get_active_user_or_raise(
            user_id=user_id, session=session
        )

        if not UserService.has_permissions(
            current_user=current_user, target_user_id=user.id
        ):
            raise exceptions.PermissionDeniedException()

        await repository.UserRepository.delete_user(session=session, user_id=user_id)

        return schemas.DeleteUserResponseSchemas(success=True)

    @staticmethod
    async def get_user_list(
        data: schemas.ListUserRequestSchemas,
        session: AsyncSession,
    ) -> schemas.ListUserResponseSchemas:
        print(data.filters)
        users, total = await repository.UserRepository.select_list_user(
            data=data, session=session
        )

        return schemas.ListUserResponseSchemas(
            data=[schemas.ListUserItemResponseSchemas(**user) for user in users],
            total=total,
            limit=data.limit,
            offset=data.offset,
        )

    @staticmethod
    async def change_password(
        data: schemas.UpdateUserPasswordRequestSchemas,
        session: AsyncSession,
        current_user: models.User,
    ) -> schemas.UpdateUserPasswordResponseSchemas:

        if not security.verify_password(data.old_password, current_user.password_hash):
            raise exceptions.OldPasswordException()

        if security.verify_password(data.new_password, current_user.password_hash):
            raise exceptions.NewPasswordException()

        new_hash = security.hash_password(data.new_password)

        await repository.UserRepository.update_password(
            user=current_user,
            new_password_hash=new_hash,
            session=session,
        )

        return schemas.UpdateUserPasswordResponseSchemas(success=True)

    @staticmethod
    async def change_email(
        data: schemas.UpdateUserEmailRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.UpdateUserEmailResponseSchemas:

        if not security.verify_password(data.password, current_user.password_hash):
            raise exceptions.InvalidCredentialsException()

        if data.new_email == current_user.email:
            raise exceptions.NewEmailMustBeDifferentException()

        existing_user = await repository.UserRepository.select_exists_user_by_email(
            email=data.new_email, session=session
        )

        if existing_user:
            raise exceptions.UserAlreadyExistsException()

        await repository.UserRepository.update_email(
            user=current_user,
            new_email=data.new_email,
            session=session,
        )

        return schemas.UpdateUserEmailResponseSchemas(success=True)

    @staticmethod
    async def change_role(
        data: schemas.UpdateUserRoleRequestSchemas,
        session: AsyncSession,
        current_user: models.User,
    ) -> schemas.UpdateUserRoleResponseSchemas:

        if data.user_id == current_user.id:
            raise exceptions.PermissionDeniedException(
                "You cannot change your own role"
            )

        target_user = await repository.UserRepository.select_user_by_id(
            user_id=data.user_id,
            session=session,
        )

        if not target_user:
            raise global_exceptions.UserNotFoundException()

        if target_user.role == data.new_role:
            raise exceptions.RoleAlreadyAssignedException()

        await repository.UserRepository.update_role(
            user_id=data.user_id,
            new_role=data.new_role,
            session=session,
        )

        return schemas.UpdateUserRoleResponseSchemas(success=True)
