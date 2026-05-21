from sqlalchemy.ext.asyncio import AsyncSession

from app.api.globals import exceptions as global_exceptions
from app.api.globals import repository as global_repository
from app.api.service import exceptions, repository, schemas
from app.api.service_type import exceptions as service_type_exceptions
from app.api.service_type import repository as service_type_repository
from app.api.user import exceptions as user_exceptions
from app.core.database import models


class ServiceService:

    @staticmethod
    async def _get_service_or_raise(
        service_id: int,
        session: AsyncSession,
    ) -> models.Service:
        service = await repository.ServiceRepository.select_service_by_id(
            service_id=service_id,
            session=session,
        )
        if not service:
            raise exceptions.ServiceNotFoundException()
        return service

    @staticmethod
    def _ensure_service_active_or_raise(service: models.Service) -> None:
        if not service.is_active:
            raise exceptions.ServiceInactiveException()

    @staticmethod
    async def _get_active_service_type_or_raise(
        service_type_id: int,
        session: AsyncSession,
    ) -> models.ServiceType:
        service_type = await service_type_repository.ServiceTypeRepository.select_service_type_by_id(  # noqa: E501
            service_type_id=service_type_id,
            session=session,
        )
        if not service_type:
            raise service_type_exceptions.ServiceTypeNotFoundException()
        if not service_type.is_active:
            raise exceptions.InactiveServiceTypeException()
        return service_type

    @staticmethod
    async def _get_master_or_raise(
        master_id: int,
        session: AsyncSession,
    ) -> models.User:
        master = await global_repository.GloablUserRepository.select_user_by_id(
            user_id=master_id,
            session=session,
        )
        if not master or not master.is_active:
            raise global_exceptions.UserNotFoundException()
        if master.role != models.RoleType.MASTER:
            raise exceptions.MasterOnlyException()
        return master

    @staticmethod
    def _ensure_service_owner_or_admin(
        current_user: models.User,
        service: models.Service,
    ) -> None:
        if current_user.role == models.RoleType.ADMIN:
            return
        if (
            current_user.role == models.RoleType.MASTER
            and current_user.id == service.master_id
        ):
            return
        raise user_exceptions.PermissionDeniedException()

    @staticmethod
    def _resolve_master_id(
        current_user: models.User,
        requested_master_id: int | None,
    ) -> int:
        if current_user.role == models.RoleType.ADMIN:
            if requested_master_id is None:
                raise exceptions.MasterIdRequiredException()
            return requested_master_id

        if current_user.role == models.RoleType.MASTER:
            if (
                requested_master_id is not None
                and requested_master_id != current_user.id
            ):
                raise user_exceptions.PermissionDeniedException()
            return current_user.id

        raise user_exceptions.PermissionDeniedException()

    @staticmethod
    async def _ensure_master_service_type_unique(
        master_id: int,
        service_type_id: int,
        session: AsyncSession,
        exclude_service_id: int | None = None,
    ) -> None:
        existing = (
            await repository.ServiceRepository.select_exists_service_by_master_and_type(
                master_id=master_id,
                service_type_id=service_type_id,
                session=session,
                exclude_service_id=exclude_service_id,
            )
        )
        if existing:
            raise exceptions.ServiceAlreadyExistsException()

    @staticmethod
    async def create_service(
        data: schemas.CreateServiceRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.CreateServiceResponseSchemas:
        master_id = ServiceService._resolve_master_id(
            current_user=current_user,
            requested_master_id=data.master_id,
        )
        await ServiceService._get_master_or_raise(master_id=master_id, session=session)
        await ServiceService._get_active_service_type_or_raise(
            service_type_id=data.service_type_id,
            session=session,
        )
        await ServiceService._ensure_master_service_type_unique(
            master_id=master_id,
            service_type_id=data.service_type_id,
            session=session,
        )

        insert_data = data.model_dump(exclude={"master_id"})
        insert_data["master_id"] = master_id

        service = await repository.ServiceRepository.insert_service(
            data=insert_data,
            session=session,
        )
        return schemas.CreateServiceResponseSchemas(**service)

    @staticmethod
    async def get_service(
        service_id: int,
        session: AsyncSession,
    ) -> schemas.GetServiceResponseSchemas:
        service = await ServiceService._get_service_or_raise(
            service_id=service_id,
            session=session,
        )
        return schemas.GetServiceResponseSchemas.model_validate(service)

    @staticmethod
    async def update_service(
        service_id: int,
        data: schemas.UpdateServiceRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.UpdateServiceResponseSchemas:
        service = await ServiceService._get_service_or_raise(
            service_id=service_id,
            session=session,
        )
        ServiceService._ensure_service_owner_or_admin(
            current_user=current_user, service=service
        )
        ServiceService._ensure_service_active_or_raise(service=service)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return schemas.UpdateServiceResponseSchemas.model_validate(service)

        target_master_id = update_data.get("master_id", service.master_id)
        target_service_type_id = update_data.get(
            "service_type_id", service.service_type_id
        )

        if "master_id" in update_data:
            if current_user.role != models.RoleType.ADMIN:
                raise user_exceptions.PermissionDeniedException()
            await ServiceService._get_master_or_raise(
                master_id=target_master_id, session=session
            )

        if "service_type_id" in update_data:
            await ServiceService._get_active_service_type_or_raise(
                service_type_id=target_service_type_id,
                session=session,
            )

        await ServiceService._ensure_master_service_type_unique(
            master_id=target_master_id,
            service_type_id=target_service_type_id,
            session=session,
            exclude_service_id=service_id,
        )

        updated_service = await repository.ServiceRepository.update_service(
            service_id=service_id,
            data=update_data,
            session=session,
        )
        return schemas.UpdateServiceResponseSchemas(**updated_service)

    @staticmethod
    async def change_service_status(
        service_id: int,
        data: schemas.ChangeServiceStatusRequestSchemas,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.ChangeServiceStatusResponseSchemas:
        service = await ServiceService._get_service_or_raise(
            service_id=service_id,
            session=session,
        )
        ServiceService._ensure_service_owner_or_admin(
            current_user=current_user, service=service
        )

        if service.is_active is data.is_active:
            if data.is_active:
                raise exceptions.ServiceAlreadyActiveException()
            raise exceptions.ServiceAlreadyInactiveException()

        updated_service = await repository.ServiceRepository.update_service(
            service_id=service_id,
            data={"is_active": data.is_active},
            session=session,
        )
        return schemas.ChangeServiceStatusResponseSchemas(**updated_service)

    @staticmethod
    async def delete_service(
        service_id: int,
        current_user: models.User,
        session: AsyncSession,
    ) -> schemas.DeleteServiceResponseSchemas:
        service = await ServiceService._get_service_or_raise(
            service_id=service_id,
            session=session,
        )
        ServiceService._ensure_service_owner_or_admin(
            current_user=current_user, service=service
        )
        ServiceService._ensure_service_active_or_raise(service=service)

        if service.is_active:
            await repository.ServiceRepository.update_service(
                service_id=service_id,
                data={"is_active": False},
                session=session,
            )

        return schemas.DeleteServiceResponseSchemas(success=True)

    @staticmethod
    async def get_service_list(
        data: schemas.ListServiceRequestSchemas,
        session: AsyncSession,
    ) -> schemas.ListServiceResponseSchemas:
        services, total = await repository.ServiceRepository.select_list_service(
            data=data,
            session=session,
        )
        return schemas.ListServiceResponseSchemas(
            data=[
                schemas.ListServiceItemResponseSchemas(**service)
                for service in services
            ],
            total=total,
            limit=data.limit,
            offset=data.offset,
        )
