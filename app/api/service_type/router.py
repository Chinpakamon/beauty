from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service_type import schemas, service
from app.core.database.core import get_session
from app.core.middleware import dependencies

router = APIRouter(prefix="/service-type", tags=["ServiceType"])


@router.post("/create", response_model=schemas.CreateServiceTypeResponseSchemas)
async def create_service_type(
    data: schemas.CreateServiceTypeRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_admin),
):
    return await service.ServiceTypeService.create_service_type(
        data=data,
        session=session,
    )


@router.get("/{service_type_id:int}", response_model=schemas.GetServiceTypeResponseSchemas)
async def get_service_type(
    service_type_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await service.ServiceTypeService.get_service_type(
        service_type_id=service_type_id,
        session=session,
    )


@router.patch("/update/{service_type_id:int}", response_model=schemas.UpdateServiceTypeResponseSchemas)
async def update_service_type(
    service_type_id: int,
    data: schemas.UpdateServiceTypeRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_admin),
):
    return await service.ServiceTypeService.update_service_type(
        service_type_id=service_type_id,
        data=data,
        session=session,
    )


@router.patch(
    "/change-status/{service_type_id:int}",
    response_model=schemas.ChangeServiceTypeStatusResponseSchemas,
)
async def change_service_type_status(
    service_type_id: int,
    data: schemas.ChangeServiceTypeStatusRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_admin),
):
    return await service.ServiceTypeService.change_service_type_status(
        service_type_id=service_type_id,
        data=data,
        session=session,
    )


@router.get("/list", response_model=schemas.ListServiceTypeResponseSchemas)
async def service_type_list(
    data: schemas.ListServiceTypeRequestSchemas = Body(),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_admin),
):
    return await service.ServiceTypeService.get_service_type_list(
        data=data,
        session=session,
    )
