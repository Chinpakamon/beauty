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
    role: RoleType = RoleType.ADMIN,
) -> models.User:
    user = models.User(
        email=email,
        password_hash=hash_password("Password123!"),
        first_name="Admin",
        last_name="User",
        phone_number="+79990001122",
        role=role,
        is_active=True,
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


async def authorize_admin(
    test_app: FastAPI,
    test_session: AsyncSession,
    email: str = "service-type-admin@example.com",
) -> models.User:
    admin = await create_user(test_session, email=email, role=RoleType.ADMIN)
    test_app.dependency_overrides[dependencies.require_admin] = lambda: admin
    return admin


def assert_service_type_payload(
    body: dict,
    *,
    name: str,
    description: str | None,
    is_active: bool = True,
) -> None:
    assert "id" in body and isinstance(body["id"], int), body
    assert body["name"] == name, body
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
async def test_create_service_type_success(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)

    response = await test_client.post(
        "/service-type/create",
        json={"name": "Haircut", "description": "Hair services"},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert_service_type_payload(
        body, name="Haircut", description="Hair services", is_active=True
    )


@pytest.mark.asyncio
async def test_create_service_type_persists_in_db(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)

    response = await test_client.post(
        "/service-type/create",
        json={"name": "Manicure", "description": None},
    )
    body = response.json()
    assert response.status_code == 200, body

    service_type = await test_session.scalar(
        select(models.ServiceType).where(models.ServiceType.id == body["id"])
    )
    assert service_type is not None
    assert service_type.name == "Manicure"
    assert service_type.description is None
    assert service_type.is_active is True


@pytest.mark.asyncio
async def test_create_service_type_duplicate_name_returns_conflict(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    await create_service_type(test_session, "Massage")

    response = await test_client.post(
        "/service-type/create",
        json={"name": "massage", "description": "Duplicate by case"},
    )

    assert_error_response(
        response,
        409,
        "Service type with this name already exists",
        context="Duplicate service type: ",
    )


@pytest.mark.asyncio
async def test_create_service_type_validation_errors(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)

    short_name_response = await test_client.post(
        "/service-type/create", json={"name": "A", "description": "Too short"}
    )
    assert_validation_error_response(short_name_response, expected_field="name")

    missing_name_response = await test_client.post(
        "/service-type/create", json={"description": "Missing name"}
    )
    assert_validation_error_response(missing_name_response, expected_field="name")

    long_description_response = await test_client.post(
        "/service-type/create", json={"name": "Spa", "description": "x" * 1001}
    )
    assert_validation_error_response(
        long_description_response, expected_field="description"
    )


@pytest.mark.asyncio
async def test_get_service_type_success(
    test_client: AsyncClient, test_session: AsyncSession
):
    service_type = await create_service_type(
        test_session, "Brows", description="Brow services", is_active=False
    )

    response = await test_client.get(f"/service-type/{service_type.id}")
    body = response.json()

    assert response.status_code == 200, body
    assert body["id"] == service_type.id
    assert_service_type_payload(
        body, name="Brows", description="Brow services", is_active=False
    )


@pytest.mark.asyncio
async def test_get_service_type_not_found(test_client: AsyncClient):
    response = await test_client.get("/service-type/999999")

    assert_error_response(
        response,
        404,
        "Service type not found",
        context="Get service type: ",
    )


@pytest.mark.asyncio
async def test_update_service_type_success(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(test_session, "Original", "Old")

    response = await test_client.patch(
        f"/service-type/update/{service_type.id}",
        json={"name": "Updated", "description": "New description"},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["id"] == service_type.id
    assert_service_type_payload(
        body, name="Updated", description="New description", is_active=True
    )


@pytest.mark.asyncio
async def test_update_service_type_data_really_changed_in_db(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(test_session, "DB Original", "Old")

    response = await test_client.patch(
        f"/service-type/update/{service_type.id}",
        json={"description": "Only description changed"},
    )
    assert response.status_code == 200, response.json()

    updated = await test_session.scalar(
        select(models.ServiceType).where(models.ServiceType.id == service_type.id)
    )
    assert updated is not None
    assert updated.name == "DB Original"
    assert updated.description == "Only description changed"


@pytest.mark.asyncio
async def test_update_service_type_empty_payload_returns_existing_data(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(test_session, "Noop", "No changes")

    response = await test_client.patch(
        f"/service-type/update/{service_type.id}", json={}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["id"] == service_type.id
    assert_service_type_payload(body, name="Noop", description="No changes")


@pytest.mark.asyncio
async def test_update_service_type_duplicate_name_returns_conflict(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    first = await create_service_type(test_session, "Nails")
    await create_service_type(test_session, "Pedicure")

    response = await test_client.patch(
        f"/service-type/update/{first.id}", json={"name": "pedicure"}
    )

    assert_error_response(
        response,
        409,
        "Service type with this name already exists",
        context="Update duplicate service type: ",
    )


@pytest.mark.asyncio
async def test_update_service_type_not_found(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)

    response = await test_client.patch(
        "/service-type/update/999999", json={"name": "Missing"}
    )

    assert_error_response(
        response,
        404,
        "Service type not found",
        context="Update missing service type: ",
    )


@pytest.mark.asyncio
async def test_update_service_type_validation_error(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(test_session, "Validated")

    response = await test_client.patch(
        f"/service-type/update/{service_type.id}", json={"name": "A"}
    )

    assert_validation_error_response(response, expected_field="name")


@pytest.mark.asyncio
async def test_change_service_type_status_to_inactive_success(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(test_session, "Active Status")

    response = await test_client.patch(
        f"/service-type/change-status/{service_type.id}", json={"is_active": False}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["id"] == service_type.id
    assert_service_type_payload(
        body, name="Active Status", description="Test service type", is_active=False
    )


@pytest.mark.asyncio
async def test_change_service_type_status_to_active_success(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(
        test_session, "Inactive Status", is_active=False
    )

    response = await test_client.patch(
        f"/service-type/change-status/{service_type.id}", json={"is_active": True}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["id"] == service_type.id
    assert_service_type_payload(
        body, name="Inactive Status", description="Test service type", is_active=True
    )


@pytest.mark.asyncio
async def test_change_service_type_status_data_really_changed_in_db(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(test_session, "Persist Status")

    response = await test_client.patch(
        f"/service-type/change-status/{service_type.id}", json={"is_active": False}
    )
    assert response.status_code == 200, response.json()

    updated = await test_session.scalar(
        select(models.ServiceType).where(models.ServiceType.id == service_type.id)
    )
    assert updated is not None
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_change_service_type_status_already_active_returns_conflict(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(test_session, "Already Active")

    response = await test_client.patch(
        f"/service-type/change-status/{service_type.id}", json={"is_active": True}
    )

    assert_error_response(
        response,
        409,
        "Service type is already active",
        context="Already active service type: ",
    )


@pytest.mark.asyncio
async def test_change_service_type_status_already_inactive_returns_conflict(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(
        test_session, "Already Inactive", is_active=False
    )

    response = await test_client.patch(
        f"/service-type/change-status/{service_type.id}", json={"is_active": False}
    )

    assert_error_response(
        response,
        409,
        "Service type is already inactive",
        context="Already inactive service type: ",
    )


@pytest.mark.asyncio
async def test_change_service_type_status_not_found(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)

    response = await test_client.patch(
        "/service-type/change-status/999999", json={"is_active": False}
    )

    assert_error_response(
        response,
        404,
        "Service type not found",
        context="Change missing service type status: ",
    )


@pytest.mark.asyncio
async def test_change_service_type_status_validation_error(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    service_type = await create_service_type(test_session, "Status Validation")

    response = await test_client.patch(
        f"/service-type/change-status/{service_type.id}", json={}
    )

    assert_validation_error_response(response, expected_field="is_active")


@pytest.mark.asyncio
async def test_service_type_list_returns_service_types(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    await create_service_type(test_session, "List One")
    await create_service_type(test_session, "List Two")

    response = await test_client.request("GET", "/service-type/list", json={})
    body = response.json()

    assert response.status_code == 200, body
    assert body["total"] == 2, body
    assert body["limit"] == 10, body
    assert body["offset"] == 0, body
    assert {item["name"] for item in body["data"]} == {"List One", "List Two"}


@pytest.mark.asyncio
async def test_service_type_list_pagination_works(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    await create_service_type(test_session, "Page One")
    await create_service_type(test_session, "Page Two")

    response = await test_client.request(
        "GET", "/service-type/list", json={"limit": 1, "offset": 1}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert len(body["data"]) == 1, body
    assert body["total"] == 2, body
    assert body["limit"] == 1, body
    assert body["offset"] == 1, body


@pytest.mark.asyncio
async def test_service_type_list_filter_by_name_works(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    await create_service_type(test_session, "Hair Color")
    await create_service_type(test_session, "Nail Care")

    response = await test_client.request(
        "GET", "/service-type/list", json={"filters": {"name": "hair"}}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["total"] == 1, body
    assert [item["name"] for item in body["data"]] == ["Hair Color"]


@pytest.mark.asyncio
async def test_service_type_list_filter_by_status_works(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    await create_service_type(test_session, "Visible", is_active=True)
    await create_service_type(test_session, "Hidden", is_active=False)

    response = await test_client.request(
        "GET", "/service-type/list", json={"filters": {"is_active": False}}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["total"] == 1, body
    assert body["data"][0]["name"] == "Hidden", body
    assert body["data"][0]["is_active"] is False, body


@pytest.mark.asyncio
async def test_service_type_list_sort_by_name_works(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    await create_service_type(test_session, "Zen")
    await create_service_type(test_session, "Aroma")

    response = await test_client.request(
        "GET", "/service-type/list", json={"order_by": "NAME_ASC"}
    )
    body = response.json()

    assert response.status_code == 200, body
    names = [item["name"] for item in body["data"]]
    assert names == sorted(names), body


@pytest.mark.asyncio
async def test_service_type_list_empty_returns_correctly(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)
    await create_service_type(test_session, "Existing")

    response = await test_client.request(
        "GET", "/service-type/list", json={"filters": {"name": "missing"}}
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["data"] == [], body
    assert body["total"] == 0, body


@pytest.mark.asyncio
async def test_service_type_list_validation_error(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    await authorize_admin(test_app, test_session)

    response = await test_client.request(
        "GET", "/service-type/list", json={"limit": 0, "offset": -1}
    )

    assert_validation_error_response(response, expected_field="limit")
