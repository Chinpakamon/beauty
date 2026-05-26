from fastapi import FastAPI
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import models
from app.core.database.models.user import RoleType
from app.core.middleware.dependencies import get_current_user_dep
from app.core.security.hashing import hash_password, verify_password
from tests.conftest import load_mock


async def create_user(
    session: AsyncSession,
    email: str,
    password: str = "Password123!",
    first_name: str = "John",
    last_name: str | None = "Doe",
    phone_number: str = "+79990001122",
    role: RoleType = RoleType.USER,
) -> models.User:
    user = models.User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def assert_json_contains(actual: dict, expected: dict, context: str = "") -> None:
    for key, expected_value in expected.items():
        actual_value = actual.get(key, None)
        assert actual_value == expected_value, (
            f"{context}Mismatch for key '{key}': expected={expected_value!r}, "
            f"actual={actual_value!r}. Full response body: {actual}"
        )


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
    response, expected_status: int = 422, expected_field: str | None = None
) -> None:
    body = response.json()
    assert response.status_code == expected_status, body
    assert isinstance(body.get("detail"), list), (
        f"Validation response must contain list detail. Body: {body}"
    )
    assert body["detail"], f"Validation detail list must not be empty. Body: {body}"

    if expected_field:
        assert any(expected_field in item.get("loc", []) for item in body["detail"]), (
            f"Expected validation error for field '{expected_field}'. Body: {body}"
        )


@pytest.mark.asyncio
async def test_registration_success(test_client: AsyncClient):
    payload = load_mock("requests", "registration_success.json")
    response = await test_client.post("/user/registration", json=payload)
    body = response.json()
    assert response.status_code == 200, body
    assert_json_contains(
        body,
        load_mock("responses", "registration_success_expected.json"),
        context="Registration success: ",
    )


@pytest.mark.asyncio
async def test_registration_email_already_exists(test_client: AsyncClient):
    payload = load_mock("requests", "registration_success.json")
    await test_client.post("/user/registration", json=payload)
    response = await test_client.post("/user/registration", json=payload)
    expected_error = load_mock("errors", "registration_duplicate_email.json")
    assert_error_response(
        response,
        expected_status=expected_error["status_code"],
        expected_detail=expected_error["detail"],
        context="Duplicate registration: ",
    )


@pytest.mark.asyncio
async def test_registration_invalid_email(test_client: AsyncClient):
    response = await test_client.post(
        "/user/registration",
        json=load_mock("requests", "registration_invalid_email.json"),
    )
    expected_error = load_mock("responses", "registration_status_422.json")
    body = response.json()
    assert response.status_code == expected_error["status_code"], body
    assert "detail" in body, f"Invalid email: expected validation details in body: {body}"
    assert any(item.get("loc") for item in body["detail"]), (
        f"Invalid email: validation error payload must include field locations. Body: {body}"
    )


@pytest.mark.asyncio
async def test_registration_weak_password(test_client: AsyncClient):
    response = await test_client.post(
        "/user/registration",
        json=load_mock("requests", "registration_weak_password.json"),
    )
    assert_validation_error_response(response, expected_field="password")


@pytest.mark.asyncio
async def test_registration_empty_first_name(test_client: AsyncClient):
    response = await test_client.post(
        "/user/registration",
        json=load_mock("requests", "registration_empty_first_name.json"),
    )
    assert_validation_error_response(response, expected_field="first_name")


@pytest.mark.asyncio
async def test_registration_empty_last_name(test_client: AsyncClient):
    response = await test_client.post(
        "/user/registration",
        json=load_mock("requests", "registration_empty_last_name.json"),
    )
    body = response.json()
    assert response.status_code == 200, body
    assert "id" in body and isinstance(body["id"], int), body
    assert "access_token" in body and body["access_token"], body


@pytest.mark.asyncio
async def test_registration_invalid_phone_number(test_client: AsyncClient):
    response = await test_client.post(
        "/user/registration",
        json=load_mock("requests", "registration_invalid_phone.json"),
    )
    assert_validation_error_response(response, expected_field="phone_number")


@pytest.mark.asyncio
async def test_registration_user_created_in_db(
    test_client: AsyncClient, test_session: AsyncSession
):
    payload = load_mock("requests", "registration_success.json")
    await test_client.post("/user/registration", json=payload)
    user = await test_session.scalar(
        select(models.User).where(models.User.email == payload["email"])
    )
    assert user is not None


@pytest.mark.asyncio
async def test_registration_password_saved_hashed(
    test_client: AsyncClient, test_session: AsyncSession
):
    payload = load_mock("requests", "registration_hash_password.json")
    await test_client.post("/user/registration", json=payload)
    user = await test_session.scalar(
        select(models.User).where(models.User.email == payload["email"])
    )
    assert user is not None
    assert user.password_hash != payload["password"]
    assert verify_password(payload["password"], user.password_hash)


@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient):
    await test_client.post(
        "/user/registration", json=load_mock("requests", "registration_success.json")
    )
    response = await test_client.post(
        "/user/login", json=load_mock("requests", "login_success.json")
    )
    body = response.json()
    assert response.status_code == 200, body
    assert "access_token" in body and body["access_token"], body
    assert body.get("token_type") == "bearer", body


@pytest.mark.asyncio
async def test_login_wrong_email(test_client: AsyncClient, test_session: AsyncSession):
    await create_user(test_session, "login@example.com")
    response = await test_client.post(
        "/user/login", json=load_mock("requests", "login_invalid_email.json")
    )
    assert_error_response(
        response, 401, "Invalid email or password", "Wrong password: "
    )


@pytest.mark.asyncio
async def test_login_wrong_password(
    test_client: AsyncClient, test_session: AsyncSession
):
    await create_user(test_session, "login@example.com")
    response = await test_client.post(
        "/user/login", json=load_mock("requests", "login_invalid_password.json")
    )
    assert response.status_code == 401, response.json()


@pytest.mark.asyncio
async def test_login_returns_access_token_and_bearer(test_client: AsyncClient):
    await test_client.post(
        "/user/registration", json=load_mock("requests", "registration_success.json")
    )
    response = await test_client.post(
        "/user/login", json=load_mock("requests", "login_success.json")
    )
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(test_client: AsyncClient):
    response = await test_client.get("/user/me")
    assert response.status_code in (401, 422), response.json()


@pytest.mark.asyncio
async def test_me_with_valid_user_returns_current_user(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    user = await create_user(test_session, "me@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: user
    response = await test_client.get("/user/me")
    body = response.json()
    assert response.status_code == 200, body
    assert body["email"] == user.email, body
    assert body["id"] == user.id, body
    assert body["role"] == user.role.value, body


@pytest.mark.asyncio
async def test_me_not_return_password_fields(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    user = await create_user(test_session, "me2@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: user
    response = await test_client.get("/user/me")
    body = response.json()
    assert "password" not in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_get_existing_user(test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession):
    current = await create_user(test_session, "current@example.com")
    target = await create_user(test_session, "target@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: current
    response = await test_client.get(f"/user/{target.id}")
    body = response.json()
    assert response.status_code == 200, body
    assert body["id"] == target.id, body
    assert body["email"] == target.email, body


@pytest.mark.asyncio
async def test_get_nonexistent_user(
    test_client: AsyncClient, test_app:FastAPI, test_session: AsyncSession
):
    current = await create_user(test_session, "current2@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: current
    response = await test_client.get("/user/999999")
    assert_error_response(response, 404, "User not found", context="Get user: ")


@pytest.mark.asyncio
async def test_get_user_without_auth_forbidden(test_client: AsyncClient):
    response = await test_client.get("/user/1")
    assert response.status_code in (401, 422), response.json()


@pytest.mark.asyncio
async def test_update_user_can_update_self(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    user = await create_user(test_session, "updself@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: user
    response = await test_client.post(
        f"/user/update/{user.id}", json=load_mock("requests", "update_self.json")
    )
    body = response.json()
    assert response.status_code == 200, body
    assert body["id"] == user.id, body
    assert body["first_name"] == "SelfUpdated", body


@pytest.mark.asyncio
async def test_update_user_cannot_update_other_as_user(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    user = await create_user(test_session, "upd1@example.com")
    other = await create_user(test_session, "upd2@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: user
    response = await test_client.post(
        f"/user/update/{other.id}", json=load_mock("requests", "update_self.json")
    )
    assert_error_response(
        response,
        403,
        "You do not have sufficient permissions/rights to perform this operation",
        context="Update user: ",
    )


@pytest.mark.asyncio
async def test_update_user_admin_can_update_other(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    admin = await create_user(test_session, "updadmin@example.com", role=RoleType.ADMIN)
    other = await create_user(test_session, "updother@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: admin
    response = await test_client.post(
        f"/user/update/{other.id}", json=load_mock("requests", "update_admin.json")
    )
    body = response.json()
    assert response.status_code == 200, body
    assert body["id"] == other.id, body
    assert body["first_name"] == "UpdatedByAdmin", body


@pytest.mark.asyncio
async def test_update_user_data_really_changed_in_db(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    user = await create_user(test_session, "updreal@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: user
    await test_client.post(
        f"/user/update/{user.id}", json=load_mock("requests", "update_self.json")
    )
    updated = await test_session.scalar(
        select(models.User).where(models.User.id == user.id)
    )
    assert updated.first_name == "SelfUpdated"


@pytest.mark.asyncio
async def test_delete_user_can_delete_self(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    user = await create_user(test_session, "delself@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: user
    response = await test_client.post(f"/user/delete/{user.id}")
    body = response.json()
    assert response.status_code == 200, body
    assert body == {"success": True}, body


@pytest.mark.asyncio
async def test_delete_user_cannot_delete_other_as_user(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    user = await create_user(test_session, "del1@example.com")
    other = await create_user(test_session, "del2@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: user
    response = await test_client.post(f"/user/delete/{other.id}")
    assert_error_response(
        response,
        403,
        "You do not have sufficient permissions/rights to perform this operation",
        context="Delete user: ",
    )


@pytest.mark.asyncio
async def test_delete_user_admin_can_delete_other(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    admin = await create_user(test_session, "deladmin@example.com", role=RoleType.ADMIN)
    other = await create_user(test_session, "delother@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: admin
    response = await test_client.post(f"/user/delete/{other.id}")
    body = response.json()
    assert response.status_code == 200, body
    assert body == {"success": True}, body


@pytest.mark.asyncio
async def test_delete_user_nonexistent(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    admin = await create_user(
        test_session, "deladmin2@example.com", role=RoleType.ADMIN
    )
    test_app.dependency_overrides[get_current_user_dep] = lambda: admin
    response = await test_client.post("/user/delete/999999")
    assert_error_response(response, 404, "User not found", context="Delete user: ")


@pytest.mark.asyncio
async def test_delete_user_becomes_inactive(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    user = await create_user(test_session, "delinactive@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: user
    await test_client.post(f"/user/delete/{user.id}")
    deleted = await test_session.scalar(
        select(models.User).where(models.User.id == user.id)
    )
    assert deleted.is_active is False


@pytest.mark.asyncio
async def test_user_list_returns_users(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    admin = await create_user(
        test_session, "listadmin@example.com", role=RoleType.ADMIN
    )
    await create_user(test_session, "lista@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: admin
    response = await test_client.request(
        "GET", "/user/list", json=load_mock("requests", "user_list_default.json")
    )
    body = response.json()
    assert response.status_code == 200, body
    assert len(body["data"]) >= 1, body
    assert {"data", "total", "limit", "offset"}.issubset(body.keys()), body


@pytest.mark.asyncio
async def test_user_list_pagination_works(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    admin = await create_user(
        test_session, "listadmin2@example.com", role=RoleType.ADMIN
    )
    await create_user(test_session, "listb1@example.com")
    await create_user(test_session, "listb2@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: admin
    response = await test_client.request(
        "GET", "/user/list", json=load_mock("requests", "user_list_pagination.json")
    )
    body = response.json()
    assert response.status_code == 200, body
    assert len(body["data"]) <= 1, body
    assert body["limit"] == 1, body


@pytest.mark.asyncio
async def test_user_list_filter_works(
    test_client: AsyncClient, test_app:FastAPI, test_session: AsyncSession
):
    admin = await create_user(
        test_session, "listadmin3@example.com", role=RoleType.ADMIN
    )
    await create_user(test_session, "listfilter@example.com", first_name="List1")
    test_app.dependency_overrides[get_current_user_dep] = lambda: admin
    response = await test_client.request(
        "GET", "/user/list", json=load_mock("requests", "user_list_filter.json")
    )
    body = response.json()
    assert response.status_code == 200, body
    assert any(item["first_name"] == "List1" for item in body["data"]), body


@pytest.mark.asyncio
async def test_user_list_sort_works(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    admin = await create_user(
        test_session, "listadmin4@example.com", role=RoleType.ADMIN
    )
    await create_user(test_session, "za@example.com")
    await create_user(test_session, "aa@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: admin
    response = await test_client.request(
        "GET", "/user/list", json=load_mock("requests", "user_list_sort.json")
    )
    body = response.json()
    assert response.status_code == 200, body
    emails = [item["email"] for item in body["data"]]
    assert emails == sorted(emails), body


@pytest.mark.asyncio
async def test_user_list_empty_returns_correctly(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    admin = await create_user(
        test_session, "listadmin5@example.com", role=RoleType.ADMIN
    )
    test_app.dependency_overrides[get_current_user_dep] = lambda: admin
    response = await test_client.request(
        "GET", "/user/list", json=load_mock("requests", "user_list_empty_filter.json")
    )
    body = response.json()
    assert response.status_code == 200, body
    assert body["data"] == [], body
    assert body["total"] == 0, body


@pytest.mark.asyncio
async def test_change_email_cannot_set_busy_email(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    user = await create_user(test_session, "busyself@example.com")
    await create_user(test_session, "other@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: user
    response = await test_client.patch(
        "/user/change-email", json=load_mock("requests", "change_email_busy.json")
    )
    assert_error_response(
        response,
        409,
        "User with this email already exists",
        context="Change email: ",
    )
