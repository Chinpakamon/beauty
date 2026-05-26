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


@pytest.mark.asyncio
async def test_registration_success(test_client: AsyncClient):
    payload = load_mock("requests", "registration_success.json")
    response = await test_client.post("/user/registration", json=payload)
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_registration_email_already_exists(test_client: AsyncClient):
    payload = load_mock("requests", "registration_success.json")
    await test_client.post("/user/registration", json=payload)
    response = await test_client.post("/user/registration", json=payload)
    assert response.status_code == 409, response.json()


@pytest.mark.asyncio
async def test_registration_invalid_email(test_client: AsyncClient):
    response = await test_client.post(
        "/user/registration",
        json=load_mock("requests", "registration_invalid_email.json"),
    )
    assert response.status_code == 422, response.json()


@pytest.mark.asyncio
async def test_registration_weak_password(test_client: AsyncClient):
    response = await test_client.post(
        "/user/registration",
        json=load_mock("requests", "registration_weak_password.json"),
    )
    assert response.status_code == 422, response.json()


@pytest.mark.asyncio
async def test_registration_empty_first_name(test_client: AsyncClient):
    response = await test_client.post(
        "/user/registration",
        json=load_mock("requests", "registration_empty_first_name.json"),
    )
    assert response.status_code == 422, response.json()


@pytest.mark.asyncio
async def test_registration_empty_last_name(test_client: AsyncClient):
    response = await test_client.post(
        "/user/registration",
        json=load_mock("requests", "registration_empty_last_name.json"),
    )
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_registration_invalid_phone_number(test_client: AsyncClient):
    response = await test_client.post(
        "/user/registration",
        json=load_mock("requests", "registration_invalid_phone.json"),
    )
    assert response.status_code == 422, response.json()


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
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_login_wrong_email(test_client: AsyncClient, test_session: AsyncSession):
    await create_user(test_session, "login@example.com")
    response = await test_client.post(
        "/user/login", json=load_mock("requests", "login_invalid_email.json")
    )
    assert response.status_code == 401, response.json()


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
    assert response.status_code == 200, response.json()
    assert response.json()["email"] == user.email


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
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_get_nonexistent_user(
    test_client: AsyncClient, test_app:FastAPI, test_session: AsyncSession
):
    current = await create_user(test_session, "current2@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: current
    response = await test_client.get("/user/999999")
    assert response.status_code == 404, response.json()


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
    assert response.status_code == 200, response.json()


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
    assert response.status_code == 403, response.json()


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
    assert response.status_code == 200, response.json()


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
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_delete_user_cannot_delete_other_as_user(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    user = await create_user(test_session, "del1@example.com")
    other = await create_user(test_session, "del2@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: user
    response = await test_client.post(f"/user/delete/{other.id}")
    assert response.status_code == 403, response.json()


@pytest.mark.asyncio
async def test_delete_user_admin_can_delete_other(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    admin = await create_user(test_session, "deladmin@example.com", role=RoleType.ADMIN)
    other = await create_user(test_session, "delother@example.com")
    test_app.dependency_overrides[get_current_user_dep] = lambda: admin
    response = await test_client.post(f"/user/delete/{other.id}")
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_delete_user_nonexistent(
    test_client: AsyncClient, test_app: FastAPI, test_session: AsyncSession
):
    admin = await create_user(
        test_session, "deladmin2@example.com", role=RoleType.ADMIN
    )
    test_app.dependency_overrides[get_current_user_dep] = lambda: admin
    response = await test_client.post("/user/delete/999999")
    assert response.status_code == 404, response.json()


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
    assert response.status_code == 200, response.json()
    assert len(response.json()["data"]) >= 1


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
    assert response.status_code == 200, response.json()
    assert len(response.json()["data"]) <= 1


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
    assert response.status_code == 200, response.json()


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
    assert response.status_code == 200, response.json()


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
    assert response.status_code == 200, response.json()
    assert response.json()["data"] == []


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
    assert response.status_code == 409, response.json()
