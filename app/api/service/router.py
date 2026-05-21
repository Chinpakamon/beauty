from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service import schemas, service
from app.core.database.core import get_session
from app.core.middleware import dependencies

router = APIRouter(prefix="/service", tags=["Service"])


@router.post("/create", response_model=schemas.CreateServiceResponseSchemas)
async def create_service(
    data: schemas.CreateServiceRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_master_or_admin),
):
    return await service.ServiceService.create_service(
        data=data,
        current_user=current_user,
        session=session,
    )


@router.get("/{service_id:int}", response_model=schemas.GetServiceResponseSchemas)
async def get_service(
    service_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await service.ServiceService.get_service(
        service_id=service_id,
        session=session,
    )


@router.patch(
    "/update/{service_id:int}", response_model=schemas.UpdateServiceResponseSchemas
)
async def update_service(
    service_id: int,
    data: schemas.UpdateServiceRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_master_or_admin),
):
    return await service.ServiceService.update_service(
        service_id=service_id,
        data=data,
        current_user=current_user,
        session=session,
    )


@router.patch(
    "/change-status/{service_id:int}",
    response_model=schemas.ChangeServiceStatusResponseSchemas,
)
async def change_service_status(
    service_id: int,
    data: schemas.ChangeServiceStatusRequestSchemas,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_master_or_admin),
):
    return await service.ServiceService.change_service_status(
        service_id=service_id,
        data=data,
        current_user=current_user,
        session=session,
    )


@router.delete(
    "/delete/{service_id:int}", response_model=schemas.DeleteServiceResponseSchemas
)
async def delete_service(
    service_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(dependencies.require_master_or_admin),
):
    return await service.ServiceService.delete_service(
        service_id=service_id,
        current_user=current_user,
        session=session,
    )


@router.get("/list", response_model=schemas.ListServiceResponseSchemas)
async def service_list(
    data: schemas.ListServiceRequestSchemas = Body(),
    session: AsyncSession = Depends(get_session),
):
    return await service.ServiceService.get_service_list(
        data=data,
        session=session,
    )
