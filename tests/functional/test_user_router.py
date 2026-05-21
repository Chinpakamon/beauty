import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.globals import exceptions as global_exceptions
from app.api.user import exceptions as user_exceptions
from app.api.user import schemas
from app.api.user.router import router
from app.api.user.service import UserService
from app.core.database.core import get_session
from app.core.middleware.dependencies import get_current_user_dep, require_admin

MOCKS_DIR = Path(__file__).resolve().parents[1] / "mocks" / "user"


def load_mock(*parts: str) -> dict:
    return json.loads((MOCKS_DIR.joinpath(*parts)).read_text())


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)

    async def override_session():
        yield None

    app.dependency_overrides[get_session] = override_session
    return TestClient(app)


def test_registration_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    success_response = load_mock("success", "registration.json")
    monkeypatch.setattr(
        UserService,
        "registration_user",
        AsyncMock(
            return_value=schemas.RegistrationUserResponseSchemas(**success_response)
        ),
    )

    response = client.post(
        "/user/registration",
        json={
            "email": "user@example.com",
            "password": "Password123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+79998887766",
        },
    )

    assert response.status_code == 200
    assert response.json() == success_response


def test_registration_user_exists_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "user_exists.json")
    monkeypatch.setattr(
        UserService,
        "registration_user",
        AsyncMock(side_effect=user_exceptions.UserAlreadyExistsException()),
    )

    response = client.post(
        "/user/registration",
        json={
            "email": "user@example.com",
            "password": "Password123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+79998887766",
        },
    )

    assert response.status_code == 409
    assert response.json() == error_response


def test_login_invalid_credentials(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "invalid_credentials.json")
    monkeypatch.setattr(
        UserService,
        "login",
        AsyncMock(side_effect=user_exceptions.InvalidCredentialsException()),
    )

    response = client.post(
        "/user/login",
        json={"email": "user@example.com", "password": "Password123!"},
    )

    assert response.status_code == 401
    assert response.json() == error_response


def test_login_success(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    success_response = load_mock("success", "login.json")
    monkeypatch.setattr(
        UserService,
        "login",
        AsyncMock(return_value=schemas.LoginUserResponseSchemas(**success_response)),
    )

    response = client.post(
        "/user/login",
        json={"email": "user@example.com", "password": "Password123!"},
    )

    assert response.status_code == 200
    assert response.json() == success_response


def test_me_success(client: TestClient) -> None:
    success_response = load_mock("success", "me.json")
    current_user = SimpleNamespace(
        id=10,
        email="me@example.com",
        first_name="Me",
        last_name="User",
        role=SimpleNamespace(value="USER"),
        phone_number="+79990001122",
    )

    client.app.dependency_overrides[get_current_user_dep] = lambda: current_user
    response = client.get("/user/me")

    assert response.status_code == 200
    assert response.json() == success_response


def test_me_unauthorized(client: TestClient) -> None:
    error_response = load_mock("errors", "unauthorized.json")

    def unauthorized_override():
        raise global_exceptions.UnauthorizedException()

    client.app.dependency_overrides[get_current_user_dep] = unauthorized_override
    response = client.get("/user/me")

    assert response.status_code == 401
    assert response.json() == error_response


def test_get_user_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "user_not_found.json")
    current_user = SimpleNamespace(id=1, role=SimpleNamespace(value="ADMIN"))
    client.app.dependency_overrides[get_current_user_dep] = lambda: current_user
    monkeypatch.setattr(
        UserService,
        "get_user",
        AsyncMock(side_effect=global_exceptions.UserNotFoundException()),
    )

    response = client.get("/user/999")

    assert response.status_code == 404
    assert response.json() == error_response


def test_update_user_permission_denied(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "permission_denied.json")
    current_user = SimpleNamespace(id=1, role=SimpleNamespace(value="USER"))
    client.app.dependency_overrides[get_current_user_dep] = lambda: current_user
    monkeypatch.setattr(
        UserService,
        "update_user",
        AsyncMock(side_effect=user_exceptions.PermissionDeniedException()),
    )

    response = client.post(
        "/user/update/2",
        json={"first_name": "Updated", "phone_number": "+79991112233"},
    )

    assert response.status_code == 403
    assert response.json() == error_response


def test_update_user_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    success_response = load_mock("success", "update_user.json")
    current_user = SimpleNamespace(id=1, role=SimpleNamespace(value="ADMIN"))
    client.app.dependency_overrides[get_current_user_dep] = lambda: current_user
    monkeypatch.setattr(
        UserService,
        "update_user",
        AsyncMock(return_value=schemas.UpdateUserResponseSchemas(**success_response)),
    )

    response = client.post(
        "/user/update/2",
        json={"first_name": "Updated", "phone_number": "+79991112233"},
    )

    assert response.status_code == 200
    assert response.json() == success_response


def test_delete_user_permission_denied(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "permission_denied.json")
    current_user = SimpleNamespace(id=1, role=SimpleNamespace(value="USER"))
    client.app.dependency_overrides[get_current_user_dep] = lambda: current_user
    monkeypatch.setattr(
        UserService,
        "delete_user",
        AsyncMock(side_effect=user_exceptions.PermissionDeniedException()),
    )

    response = client.post("/user/delete/2")

    assert response.status_code == 403
    assert response.json() == error_response


def test_delete_user_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    success_response = load_mock("success", "delete_user.json")
    current_user = SimpleNamespace(id=1, role=SimpleNamespace(value="ADMIN"))
    client.app.dependency_overrides[get_current_user_dep] = lambda: current_user
    monkeypatch.setattr(
        UserService,
        "delete_user",
        AsyncMock(return_value=schemas.DeleteUserResponseSchemas(**success_response)),
    )

    response = client.post("/user/delete/2")

    assert response.status_code == 200
    assert response.json() == success_response


def test_user_list_success(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    success_response = load_mock("success", "list_user.json")
    monkeypatch.setattr(
        UserService,
        "get_user_list",
        AsyncMock(return_value=schemas.ListUserResponseSchemas(**success_response)),
    )

    response = client.request(
        "GET",
        "/user/list",
        json={"filters": {"role": "USER"}, "limit": 10, "offset": 0},
    )

    assert response.status_code == 200
    assert response.json() == success_response


def test_change_password_old_password_invalid(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "old_password_invalid.json")
    current_user = SimpleNamespace(id=1, role=SimpleNamespace(value="USER"))
    client.app.dependency_overrides[get_current_user_dep] = lambda: current_user
    monkeypatch.setattr(
        UserService,
        "change_password",
        AsyncMock(side_effect=user_exceptions.OldPasswordException()),
    )

    response = client.patch(
        "/user/change-password",
        json={"old_password": "old", "new_password": "Password123!"},
    )

    assert response.status_code == 403
    assert response.json() == error_response


def test_change_password_new_password_same(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "new_password_same.json")
    current_user = SimpleNamespace(id=1, role=SimpleNamespace(value="USER"))
    client.app.dependency_overrides[get_current_user_dep] = lambda: current_user
    monkeypatch.setattr(
        UserService,
        "change_password",
        AsyncMock(side_effect=user_exceptions.NewPasswordException()),
    )

    response = client.patch(
        "/user/change-password",
        json={"old_password": "old", "new_password": "Password123!"},
    )

    assert response.status_code == 403
    assert response.json() == error_response


def test_change_email_invalid_credentials(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "invalid_credentials.json")
    current_user = SimpleNamespace(id=1, role=SimpleNamespace(value="USER"))
    client.app.dependency_overrides[get_current_user_dep] = lambda: current_user
    monkeypatch.setattr(
        UserService,
        "change_email",
        AsyncMock(side_effect=user_exceptions.InvalidCredentialsException()),
    )

    response = client.patch(
        "/user/change-email",
        json={"new_email": "new@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == error_response


def test_change_email_same_email(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "new_email_same.json")
    current_user = SimpleNamespace(id=1, role=SimpleNamespace(value="USER"))
    client.app.dependency_overrides[get_current_user_dep] = lambda: current_user
    monkeypatch.setattr(
        UserService,
        "change_email",
        AsyncMock(side_effect=user_exceptions.NewEmailMustBeDifferentException()),
    )

    response = client.patch(
        "/user/change-email",
        json={"new_email": "same@example.com", "password": "Password123!"},
    )

    assert response.status_code == 403
    assert response.json() == error_response


def test_change_role_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    success_response = load_mock("success", "change_role.json")
    admin_user = SimpleNamespace(id=1, role=SimpleNamespace(value="ADMIN"))
    client.app.dependency_overrides[require_admin] = lambda: admin_user

    monkeypatch.setattr(
        UserService,
        "change_role",
        AsyncMock(
            return_value=schemas.UpdateUserRoleResponseSchemas(**success_response)
        ),
    )

    response = client.patch(
        "/user/change-role",
        json={"user_id": 2, "new_role": "MASTER"},
    )

    assert response.status_code == 200
    assert response.json() == success_response


def test_change_role_already_assigned(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "role_already_assigned.json")
    admin_user = SimpleNamespace(id=1, role=SimpleNamespace(value="ADMIN"))
    client.app.dependency_overrides[require_admin] = lambda: admin_user

    monkeypatch.setattr(
        UserService,
        "change_role",
        AsyncMock(side_effect=user_exceptions.RoleAlreadyAssignedException()),
    )

    response = client.patch(
        "/user/change-role",
        json={"user_id": 2, "new_role": "MASTER"},
    )

    assert response.status_code == 403
    assert response.json() == error_response


def test_change_role_user_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    error_response = load_mock("errors", "user_not_found.json")
    admin_user = SimpleNamespace(id=1, role=SimpleNamespace(value="ADMIN"))
    client.app.dependency_overrides[require_admin] = lambda: admin_user

    monkeypatch.setattr(
        UserService,
        "change_role",
        AsyncMock(side_effect=global_exceptions.UserNotFoundException()),
    )

    response = client.patch(
        "/user/change-role",
        json={"user_id": 200, "new_role": "MASTER"},
    )

    assert response.status_code == 404
    assert response.json() == error_response
