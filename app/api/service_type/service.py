from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service_type import exceptions, repository, schemas
from app.core.database import models


class ServiceTypeService:

    @staticmethod
    async def _get_service_type_or_raise(
        service_type_id: int,
        session: AsyncSession,
    ) -> models.ServiceType:
        service_type = await repository.ServiceTypeRepository.select_service_type_by_id(
            service_type_id=service_type_id,
            session=session,
        )
        if not service_type:
            raise exceptions.ServiceTypeNotFoundException()
        return service_type

    @staticmethod
    async def create_service_type(
        data: schemas.CreateServiceTypeRequestSchemas,
        session: AsyncSession,
    ) -> schemas.CreateServiceTypeResponseSchemas:
        existing = (
            await repository.ServiceTypeRepository.select_exists_service_type_by_name(
                name=data.name,
                session=session,
            )
        )
        if existing:
            raise exceptions.ServiceTypeAlreadyExistsException()

        service_type = await repository.ServiceTypeRepository.insert_service_type(
            data=data.model_dump(),
            session=session,
        )

        return schemas.CreateServiceTypeResponseSchemas(**service_type)

    @staticmethod
    async def get_service_type(
        service_type_id: int,
        session: AsyncSession,
    ) -> schemas.GetServiceTypeResponseSchemas:
        service_type = await ServiceTypeService._get_service_type_or_raise(
            service_type_id=service_type_id,
            session=session,
        )

        return schemas.GetServiceTypeResponseSchemas.model_validate(service_type)

    @staticmethod
    async def update_service_type(
        service_type_id: int,
        data: schemas.UpdateServiceTypeRequestSchemas,
        session: AsyncSession,
    ) -> schemas.UpdateServiceTypeResponseSchemas:
        service_type = await ServiceTypeService._get_service_type_or_raise(
            service_type_id=service_type_id,
            session=session,
        )

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return schemas.UpdateServiceTypeResponseSchemas.model_validate(service_type)

        if "name" in update_data:
            existing = await repository.ServiceTypeRepository.select_exists_service_type_by_name(  # noqa: E501
                name=update_data["name"],
                session=session,
                exclude_service_type_id=service_type_id,
            )
            if existing:
                raise exceptions.ServiceTypeAlreadyExistsException()

        updated_service_type = (
            await repository.ServiceTypeRepository.update_service_type(
                service_type_id=service_type_id,
                data=update_data,
                session=session,
            )
        )

        return schemas.UpdateServiceTypeResponseSchemas(**updated_service_type)

    @staticmethod
    async def change_service_type_status(
        service_type_id: int,
        data: schemas.ChangeServiceTypeStatusRequestSchemas,
        session: AsyncSession,
    ) -> schemas.ChangeServiceTypeStatusResponseSchemas:
        service_type = await ServiceTypeService._get_service_type_or_raise(
            service_type_id=service_type_id,
            session=session,
        )

        if service_type.is_active is data.is_active:
            if data.is_active:
                raise exceptions.ServiceTypeAlreadyActiveException()
            raise exceptions.ServiceTypeAlreadyInactiveException()

        updated_service_type = (
            await repository.ServiceTypeRepository.update_service_type(
                service_type_id=service_type_id,
                data={"is_active": data.is_active},
                session=session,
            )
        )

        return schemas.ChangeServiceTypeStatusResponseSchemas(**updated_service_type)

    @staticmethod
    async def get_service_type_list(
        data: schemas.ListServiceTypeRequestSchemas,
        session: AsyncSession,
    ) -> schemas.ListServiceTypeResponseSchemas:
        service_types, total = (
            await repository.ServiceTypeRepository.select_list_service_type(
                data=data,
                session=session,
            )
        )

        return schemas.ListServiceTypeResponseSchemas(
            data=[
                schemas.ListServiceTypeItemResponseSchemas(**service_type)
                for service_type in service_types
            ],
            total=total,
            limit=data.limit,
            offset=data.offset,
        )
