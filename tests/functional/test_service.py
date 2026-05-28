import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import models
from app.core.database.models.user import RoleType
from app.core.middleware import dependencies
from app.core.security.hashing import hash_password


async def create_user(
    session: AsyncSession,
    email: str,
    role: RoleType = RoleType.MASTER,
    is_active: bool = True,
) -> models.User:
    user = models.User(
        email=email,
        password_hash=hash_password("Password123!"),
        first_name="Test",
        last_name="User",
        phone_number="+79990001122",
        role=role,
        is_active=is_active,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_service_type(
    session: AsyncSession,
    name: str,
    description: str | None = "Test service type",
    is_active: bool = True,
) -> models.ServiceType:
    service_type = models.ServiceType(
        name=name,
        description=description,
        is_active=is_active,
    )
    session.add(service_type)
    await session.commit()
    await session.refresh(service_type)
    return service_type


async def create_service(
    session: AsyncSession,
    master: models.User,
    service_type: models.ServiceType,
    price: float = 100.0,
    duration_minutes: int = 60,
    description: str | None = "Test service",
    is_active: bool = True,
) -> models.Service:
    service = models.Service(
        master_id=master.id,
        service_type_id=service_type.id,
        price=price,
        duration_minutes=duration_minutes,
        description=description,
        is_active=is_active,
    )
    session.add(service)
    await session.commit()
    await session.refresh(service)
    return service


async def authorize_user(
    test_app: FastAPI,
    test_session: AsyncSession,
    email: str = "service-master@example.com",
    role: RoleType = RoleType.MASTER,
) -> models.User:
    user = await create_user(test_session, email=email, role=role)
    test_app.dependency_overrides[dependencies.require_master_or_admin] = lambda: user
    return user


async def authorize_admin(
    test_app: FastAPI,
    test_session: AsyncSession,
    email: str = "service-admin@example.com",
) -> models.User:
    return await authorize_user(
        test_app=test_app,
        test_session=test_session,
        email=email,
        role=RoleType.ADMIN,
    )


def assert_service_payload(
    body: dict,
    *,
    service_type_id: int,
    master_id: int,
    price: float,
    duration_minutes: int,
    description: str | None,
    is_active: bool = True,
) -> None:
    assert "id" in body and isinstance(body["id"], int), body
    assert body["service_type_id"] == service_type_id, body
    assert body["master_id"] == master_id, body
    assert body["price"] == price, body
    assert body["duration_minutes"] == duration_minutes, body
    assert body["description"] == description, body
    assert body["is_active"] is is_active, body


def assert_error_response(
    response,
    expected_status: int,
    expected_detail: str | None = None,
    context: str = "",
) -> None:
    body = response.json()
    assert response.status_code == expected_status, (
        f"{context}Unexpected status code: expected={expected_status}, "
        f"actual={response.status_code}. Full response body: {body}"
    )

    if expected_detail is not None:
        actual_detail = body.get("detail")
        assert actual_detail == expected_detail, (
            f"{context}Unexpected error detail: expected={expected_detail!r}, "
            f"actual={actual_detail!r}. Full response body: {body}"
        )


def assert_validation_error_response(
    response, expected_field: str | None = None
) -> None:
    body = response.json()
    assert response.status_code == 422, body
    assert isinstance(body.get("detail"), list), body
    assert body["detail"], body

    if expected_field:
        assert any(
            expected_field in item.get("loc", []) for item in body["detail"]
        ), f"Expected validation error for field '{expected_field}'. Body: {body}"


@pytest.mark.asyncio
async def test_create_service_by_admin_success(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    master = await create_user(test_session, "admin-service-master@example.com")
    service_type = await create_service_type(test_session, "Haircut")

    response = await test_client.post(
        "/service/create",
        json={
            "service_type_id": service_type.id,
            "master_id": master.id,
            "price": 150.5,
            "duration_minutes": 45,
            "description": "Classic haircut",
        },
    )
    body = response.json()

    assert response.status_code == 200, body
    assert_service_payload(
        body,
        service_type_id=service_type.id,
        master_id=master.id,
        price=150.5,
        duration_minutes=45,
        description="Classic haircut",
    )


@pytest.mark.asyncio
async def test_create_service_by_master_uses_current_user(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Massage")

    response = await test_client.post(
        "/service/create",
        json={
            "service_type_id": service_type.id,
            "price": 250,
            "duration_minutes": 90,
            "description": None,
        },
    )
    body = response.json()

    assert response.status_code == 200, body
    assert_service_payload(
        body,
        service_type_id=service_type.id,
        master_id=master.id,
        price=250,
        duration_minutes=90,
        description=None,
    )


@pytest.mark.asyncio
async def test_create_service_persists_in_db(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    admin = await authorize_admin(test_app, test_session)
    master = await create_user(test_session, "persist-service-master@example.com")
    service_type = await create_service_type(test_session, "Brows")

    response = await test_client.post(
        "/service/create",
        json={
            "service_type_id": service_type.id,
            "master_id": master.id,
            "price": 75,
            "duration_minutes": 30,
            "description": "Brow correction",
        },
    )
    body = response.json()
    assert response.status_code == 200, body
    assert admin.role is RoleType.ADMIN

    service = await test_session.scalar(
        select(models.Service).where(models.Service.id == body["id"])
    )
    assert service is not None
    assert service.master_id == master.id
    assert service.service_type_id == service_type.id
    assert service.price == 75
    assert service.duration_minutes == 30
    assert service.description == "Brow correction"
    assert service.is_active is True


@pytest.mark.asyncio
async def test_create_service_duplicate_master_and_type_returns_conflict(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    master = await create_user(test_session, "duplicate-service-master@example.com")
    service_type = await create_service_type(test_session, "Nails")
    await create_service(test_session, master, service_type)

    response = await test_client.post(
        "/service/create",
        json={
            "service_type_id": service_type.id,
            "master_id": master.id,
            "price": 120,
            "duration_minutes": 50,
        },
    )

    assert_error_response(
        response,
        409,
        "Master already provides this service type",
        context="Duplicate service: ",
    )


@pytest.mark.asyncio
async def test_create_service_admin_requires_master_id(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(test_session, "Spa")

    response = await test_client.post(
        "/service/create",
        json={
            "service_type_id": service_type.id,
            "price": 300,
            "duration_minutes": 120,
        },
    )

    assert_error_response(
        response,
        400,
        "Admin must provide master_id",
        context="Admin missing master_id: ",
    )


@pytest.mark.asyncio
async def test_create_service_master_cannot_assign_other_master(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_user(test_app, test_session)
    other_master = await create_user(test_session, "other-service-master@example.com")
    service_type = await create_service_type(test_session, "Makeup")

    response = await test_client.post(
        "/service/create",
        json={
            "service_type_id": service_type.id,
            "master_id": other_master.id,
            "price": 180,
            "duration_minutes": 60,
        },
    )

    assert_error_response(
        response,
        403,
        "You do not have sufficient permissions/rights to perform this operation",
        context="Master assigning another master: ",
    )


@pytest.mark.asyncio
async def test_create_service_rejects_non_master_assignee(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    user = await create_user(
        test_session, "not-master-service-user@example.com", role=RoleType.USER
    )
    service_type = await create_service_type(test_session, "Cosmetology")

    response = await test_client.post(
        "/service/create",
        json={
            "service_type_id": service_type.id,
            "master_id": user.id,
            "price": 100,
            "duration_minutes": 30,
        },
    )

    assert_error_response(
        response,
        400,
        "Services can be assigned only to users with MASTER role",
        context="Non-master assignee: ",
    )


@pytest.mark.asyncio
async def test_create_service_missing_master_returns_not_found(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(test_session, "Peeling")

    response = await test_client.post(
        "/service/create",
        json={
            "service_type_id": service_type.id,
            "master_id": 999999,
            "price": 100,
            "duration_minutes": 30,
        },
    )

    assert_error_response(response, 404, "User not found", context="Missing master: ")


@pytest.mark.asyncio
async def test_create_service_missing_service_type_returns_not_found(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)

    response = await test_client.post(
        "/service/create",
        json={"service_type_id": 999999, "price": 100, "duration_minutes": 30},
    )

    assert master.role is RoleType.MASTER
    assert_error_response(
        response, 404, "Service type not found", context="Missing service type: "
    )


@pytest.mark.asyncio
async def test_create_service_rejects_inactive_service_type(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(
        test_session, "Inactive Type", is_active=False
    )

    response = await test_client.post(
        "/service/create",
        json={"service_type_id": service_type.id, "price": 100, "duration_minutes": 30},
    )

    assert master.id is not None
    assert_error_response(
        response,
        400,
        "Cannot use inactive service type",
        context="Inactive service type: ",
    )


@pytest.mark.asyncio
async def test_create_service_validation_errors(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Validation Type")

    price_response = await test_client.post(
        "/service/create",
        json={"service_type_id": service_type.id, "price": 0, "duration_minutes": 30},
    )
    assert_validation_error_response(price_response, expected_field="price")

    duration_response = await test_client.post(
        "/service/create",
        json={"service_type_id": service_type.id, "price": 100, "duration_minutes": 0},
    )
    assert_validation_error_response(
        duration_response, expected_field="duration_minutes"
    )

    description_response = await test_client.post(
        "/service/create",
        json={
            "service_type_id": service_type.id,
            "price": 100,
            "duration_minutes": 30,
            "description": "x" * 1001,
        },
    )
    assert_validation_error_response(description_response, expected_field="description")


@pytest.mark.asyncio
async def test_get_service_success(
    test_client: AsyncClient, test_session: AsyncSession
):
    master = await create_user(test_session, "get-service-master@example.com")
    service_type = await create_service_type(test_session, "Get Service")
    service = await create_service(
        test_session, master, service_type, price=130, duration_minutes=40
    )

    response = await test_client.get(f"/service/{service.id}")
    body = response.json()

    assert response.status_code == 200, body
    assert body["id"] == service.id
    assert_service_payload(
        body,
        service_type_id=service_type.id,
        master_id=master.id,
        price=130,
        duration_minutes=40,
        description="Test service",
    )


@pytest.mark.asyncio
async def test_get_service_not_found(test_client: AsyncClient):
    response = await test_client.get("/service/999999")

    assert_error_response(response, 404, "Service not found", context="Get service: ")


@pytest.mark.asyncio
async def test_update_service_success_by_admin(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    old_master = await create_user(test_session, "old-update-master@example.com")
    new_master = await create_user(test_session, "new-update-master@example.com")
    old_type = await create_service_type(test_session, "Old Type")
    new_type = await create_service_type(test_session, "New Type")
    service = await create_service(test_session, old_master, old_type)

    response = await test_client.patch(
        f"/service/update/{service.id}",
        json={
            "service_type_id": new_type.id,
            "master_id": new_master.id,
            "price": 210,
            "duration_minutes": 75,
            "description": "Updated service",
        },
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["id"] == service.id
    assert_service_payload(
        body,
        service_type_id=new_type.id,
        master_id=new_master.id,
        price=210,
        duration_minutes=75,
        description="Updated service",
    )


@pytest.mark.asyncio
async def test_update_service_success_by_owner_master(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Owner Update Type")
    service = await create_service(test_session, master, service_type)

    response = await test_client.patch(
        f"/service/update/{service.id}", json={"price": 140, "description": None}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert_service_payload(
        body,
        service_type_id=service_type.id,
        master_id=master.id,
        price=140,
        duration_minutes=60,
        description=None,
    )


@pytest.mark.asyncio
async def test_update_service_empty_payload_returns_existing_data(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Noop Type")
    service = await create_service(test_session, master, service_type, price=95)

    response = await test_client.patch(f"/service/update/{service.id}", json={})
    body = response.json()

    assert response.status_code == 200, body
    assert_service_payload(
        body,
        service_type_id=service_type.id,
        master_id=master.id,
        price=95,
        duration_minutes=60,
        description="Test service",
    )


@pytest.mark.asyncio
async def test_update_service_data_really_changed_in_db(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Persist Update Type")
    service = await create_service(test_session, master, service_type)

    response = await test_client.patch(
        f"/service/update/{service.id}", json={"duration_minutes": 35}
    )
    assert response.status_code == 200, response.json()

    updated = await test_session.scalar(
        select(models.Service).where(models.Service.id == service.id)
    )
    assert updated is not None
    assert updated.duration_minutes == 35


@pytest.mark.asyncio
async def test_update_service_duplicate_target_returns_conflict(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    master = await create_user(test_session, "update-duplicate-master@example.com")
    type_one = await create_service_type(test_session, "Duplicate Type One")
    type_two = await create_service_type(test_session, "Duplicate Type Two")
    first = await create_service(test_session, master, type_one)
    await create_service(test_session, master, type_two)

    response = await test_client.patch(
        f"/service/update/{first.id}", json={"service_type_id": type_two.id}
    )

    assert_error_response(
        response,
        409,
        "Master already provides this service type",
        context="Update duplicate service: ",
    )


@pytest.mark.asyncio
async def test_update_service_rejects_inactive_existing_service(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Inactive Existing Type")
    service = await create_service(test_session, master, service_type, is_active=False)

    response = await test_client.patch(
        f"/service/update/{service.id}", json={"price": 99}
    )

    assert_error_response(
        response,
        400,
        "Service is inactive",
        context="Update inactive service: ",
    )


@pytest.mark.asyncio
async def test_update_service_rejects_inactive_service_type(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    old_type = await create_service_type(test_session, "Active Update Type")
    inactive_type = await create_service_type(
        test_session, "Inactive Update Type", is_active=False
    )
    service = await create_service(test_session, master, old_type)

    response = await test_client.patch(
        f"/service/update/{service.id}", json={"service_type_id": inactive_type.id}
    )

    assert_error_response(
        response,
        400,
        "Cannot use inactive service type",
        context="Update inactive service type: ",
    )


@pytest.mark.asyncio
async def test_update_service_master_cannot_change_master_id(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    owner = await authorize_user(test_app, test_session)
    other_master = await create_user(test_session, "update-other-master@example.com")
    service_type = await create_service_type(test_session, "Forbidden Master Type")
    service = await create_service(test_session, owner, service_type)

    response = await test_client.patch(
        f"/service/update/{service.id}", json={"master_id": other_master.id}
    )

    assert_error_response(
        response,
        403,
        "You do not have sufficient permissions/rights to perform this operation",
        context="Master changing service owner: ",
    )


@pytest.mark.asyncio
async def test_update_service_non_owner_master_returns_forbidden(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    owner = await create_user(test_session, "service-owner@example.com")
    other_master = await authorize_user(
        test_app, test_session, email="service-non-owner@example.com"
    )
    service_type = await create_service_type(test_session, "Ownership Type")
    service = await create_service(test_session, owner, service_type)

    response = await test_client.patch(
        f"/service/update/{service.id}", json={"price": 99}
    )

    assert other_master.id != owner.id
    assert_error_response(
        response,
        403,
        "You do not have sufficient permissions/rights to perform this operation",
        context="Non-owner update: ",
    )


@pytest.mark.asyncio
async def test_update_service_not_found(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)

    response = await test_client.patch("/service/update/999999", json={"price": 99})

    assert_error_response(
        response, 404, "Service not found", context="Update missing service: "
    )


@pytest.mark.asyncio
async def test_update_service_validation_error(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Update Validation Type")
    service = await create_service(test_session, master, service_type)

    response = await test_client.patch(
        f"/service/update/{service.id}", json={"price": -1}
    )

    assert_validation_error_response(response, expected_field="price")


@pytest.mark.asyncio
async def test_change_service_status_to_inactive_success(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Status Active Type")
    service = await create_service(test_session, master, service_type)

    response = await test_client.patch(
        f"/service/change-status/{service.id}", json={"is_active": False}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert_service_payload(
        body,
        service_type_id=service_type.id,
        master_id=master.id,
        price=100,
        duration_minutes=60,
        description="Test service",
        is_active=False,
    )


@pytest.mark.asyncio
async def test_change_service_status_to_active_success(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Status Inactive Type")
    service = await create_service(test_session, master, service_type, is_active=False)

    response = await test_client.patch(
        f"/service/change-status/{service.id}", json={"is_active": True}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["id"] == service.id
    assert body["is_active"] is True, body


@pytest.mark.asyncio
async def test_change_service_status_data_really_changed_in_db(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Persist Status Type")
    service = await create_service(test_session, master, service_type)

    response = await test_client.patch(
        f"/service/change-status/{service.id}", json={"is_active": False}
    )
    assert response.status_code == 200, response.json()

    updated = await test_session.scalar(
        select(models.Service).where(models.Service.id == service.id)
    )
    assert updated is not None
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_change_service_status_already_active_returns_conflict(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Already Active Type")
    service = await create_service(test_session, master, service_type)

    response = await test_client.patch(
        f"/service/change-status/{service.id}", json={"is_active": True}
    )

    assert_error_response(
        response,
        409,
        "Service is already active",
        context="Already active service: ",
    )


@pytest.mark.asyncio
async def test_change_service_status_already_inactive_returns_conflict(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Already Inactive Type")
    service = await create_service(test_session, master, service_type, is_active=False)

    response = await test_client.patch(
        f"/service/change-status/{service.id}", json={"is_active": False}
    )

    assert_error_response(
        response,
        409,
        "Service is already inactive",
        context="Already inactive service: ",
    )


@pytest.mark.asyncio
async def test_change_service_status_non_owner_master_returns_forbidden(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    owner = await create_user(test_session, "status-owner@example.com")
    await authorize_user(test_app, test_session, email="status-non-owner@example.com")
    service_type = await create_service_type(test_session, "Status Ownership Type")
    service = await create_service(test_session, owner, service_type)

    response = await test_client.patch(
        f"/service/change-status/{service.id}", json={"is_active": False}
    )

    assert_error_response(
        response,
        403,
        "You do not have sufficient permissions/rights to perform this operation",
        context="Non-owner status change: ",
    )


@pytest.mark.asyncio
async def test_change_service_status_not_found(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)

    response = await test_client.patch(
        "/service/change-status/999999", json={"is_active": False}
    )

    assert_error_response(
        response, 404, "Service not found", context="Change missing service status: "
    )


@pytest.mark.asyncio
async def test_change_service_status_validation_error(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Status Validation Type")
    service = await create_service(test_session, master, service_type)

    response = await test_client.patch(f"/service/change-status/{service.id}", json={})

    assert_validation_error_response(response, expected_field="is_active")


@pytest.mark.asyncio
async def test_delete_service_success_deactivates_service(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Delete Type")
    service = await create_service(test_session, master, service_type)

    response = await test_client.delete(f"/service/delete/{service.id}")
    body = response.json()

    assert response.status_code == 200, body
    assert body == {"success": True}
    updated = await test_session.scalar(
        select(models.Service).where(models.Service.id == service.id)
    )
    assert updated is not None
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_delete_service_rejects_inactive_service(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    master = await authorize_user(test_app, test_session)
    service_type = await create_service_type(test_session, "Inactive Delete Type")
    service = await create_service(test_session, master, service_type, is_active=False)

    response = await test_client.delete(f"/service/delete/{service.id}")

    assert_error_response(
        response,
        400,
        "Service is inactive",
        context="Delete inactive service: ",
    )


@pytest.mark.asyncio
async def test_delete_service_non_owner_master_returns_forbidden(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    owner = await create_user(test_session, "delete-owner@example.com")
    await authorize_user(test_app, test_session, email="delete-non-owner@example.com")
    service_type = await create_service_type(test_session, "Delete Ownership Type")
    service = await create_service(test_session, owner, service_type)

    response = await test_client.delete(f"/service/delete/{service.id}")

    assert_error_response(
        response,
        403,
        "You do not have sufficient permissions/rights to perform this operation",
        context="Non-owner delete: ",
    )


@pytest.mark.asyncio
async def test_delete_service_not_found(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)

    response = await test_client.delete("/service/delete/999999")

    assert_error_response(
        response, 404, "Service not found", context="Delete missing service: "
    )


@pytest.mark.asyncio
async def test_service_list_returns_services(
    test_client: AsyncClient, test_session: AsyncSession
):
    master = await create_user(test_session, "list-master@example.com")
    first_type = await create_service_type(test_session, "List Type One")
    second_type = await create_service_type(test_session, "List Type Two")
    first = await create_service(test_session, master, first_type, price=100)
    second = await create_service(test_session, master, second_type, price=200)

    response = await test_client.request("GET", "/service/list", json={})
    body = response.json()

    assert response.status_code == 200, body
    assert body["total"] == 2, body
    assert body["limit"] == 10, body
    assert body["offset"] == 0, body
    assert {item["id"] for item in body["data"]} == {first.id, second.id}


@pytest.mark.asyncio
async def test_service_list_pagination_works(
    test_client: AsyncClient, test_session: AsyncSession
):
    master = await create_user(test_session, "pagination-master@example.com")
    first_type = await create_service_type(test_session, "Pagination Type One")
    second_type = await create_service_type(test_session, "Pagination Type Two")
    await create_service(test_session, master, first_type)
    await create_service(test_session, master, second_type)

    response = await test_client.request(
        "GET", "/service/list", json={"limit": 1, "offset": 1}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert len(body["data"]) == 1, body
    assert body["total"] == 2, body
    assert body["limit"] == 1, body
    assert body["offset"] == 1, body


@pytest.mark.asyncio
async def test_service_list_filter_by_master_and_service_type_works(
    test_client: AsyncClient, test_session: AsyncSession
):
    first_master = await create_user(test_session, "filter-master-one@example.com")
    second_master = await create_user(test_session, "filter-master-two@example.com")
    target_type = await create_service_type(test_session, "Target Filter Type")
    other_type = await create_service_type(test_session, "Other Filter Type")
    target = await create_service(test_session, first_master, target_type)
    await create_service(test_session, first_master, other_type)
    await create_service(test_session, second_master, target_type)

    response = await test_client.request(
        "GET",
        "/service/list",
        json={
            "filters": {"master_id": first_master.id, "service_type_id": target_type.id}
        },
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["total"] == 1, body
    assert body["data"][0]["id"] == target.id, body


@pytest.mark.asyncio
async def test_service_list_filter_by_status_and_price_range_works(
    test_client: AsyncClient, test_session: AsyncSession
):
    master = await create_user(test_session, "filter-price-master@example.com")
    low_type = await create_service_type(test_session, "Low Price Type")
    target_type = await create_service_type(test_session, "Target Price Type")
    inactive_type = await create_service_type(test_session, "Inactive Price Type")
    await create_service(test_session, master, low_type, price=50)
    target = await create_service(test_session, master, target_type, price=150)
    await create_service(
        test_session, master, inactive_type, price=170, is_active=False
    )

    response = await test_client.request(
        "GET",
        "/service/list",
        json={"filters": {"is_active": True, "min_price": 100, "max_price": 160}},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["total"] == 1, body
    assert body["data"][0]["id"] == target.id, body
    assert body["data"][0]["price"] == 150, body


@pytest.mark.asyncio
async def test_service_list_sort_by_price_works(
    test_client: AsyncClient, test_session: AsyncSession
):
    master = await create_user(test_session, "sort-price-master@example.com")
    expensive_type = await create_service_type(test_session, "Expensive Type")
    cheap_type = await create_service_type(test_session, "Cheap Type")
    await create_service(test_session, master, expensive_type, price=300)
    await create_service(test_session, master, cheap_type, price=100)

    response = await test_client.request(
        "GET", "/service/list", json={"order_by": "PRICE_ASC"}
    )
    body = response.json()

    assert response.status_code == 200, body
    prices = [item["price"] for item in body["data"]]
    assert prices == sorted(prices), body


@pytest.mark.asyncio
async def test_service_list_sort_by_duration_works(
    test_client: AsyncClient, test_session: AsyncSession
):
    master = await create_user(test_session, "sort-duration-master@example.com")
    short_type = await create_service_type(test_session, "Short Type")
    long_type = await create_service_type(test_session, "Long Type")
    await create_service(test_session, master, short_type, duration_minutes=30)
    await create_service(test_session, master, long_type, duration_minutes=90)

    response = await test_client.request(
        "GET", "/service/list", json={"order_by": "DURATION_DESC"}
    )
    body = response.json()

    assert response.status_code == 200, body
    durations = [item["duration_minutes"] for item in body["data"]]
    assert durations == sorted(durations, reverse=True), body


@pytest.mark.asyncio
async def test_service_list_empty_returns_correctly(
    test_client: AsyncClient, test_session: AsyncSession
):
    master = await create_user(test_session, "empty-list-master@example.com")
    service_type = await create_service_type(test_session, "Empty List Type")
    await create_service(test_session, master, service_type, price=50)

    response = await test_client.request(
        "GET", "/service/list", json={"filters": {"min_price": 1000}}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["data"] == [], body
    assert body["total"] == 0, body


@pytest.mark.asyncio
async def test_service_list_validation_error(test_client: AsyncClient):
    response = await test_client.request(
        "GET", "/service/list", json={"limit": 0, "offset": -1}
    )

    assert_validation_error_response(response, expected_field="limit")
