import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_frontend_index_contains_application_mount(test_client: AsyncClient):
    response = await test_client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="app-root"' in response.text
    assert 'href="/frontend/styles.css"' in response.text
    assert 'type="module" src="/frontend/app.js"' in response.text
    assert "Главная навигация" not in response.text


@pytest.mark.asyncio
async def test_frontend_serves_vanilla_js_entrypoint(test_client: AsyncClient):
    response = await test_client.get("/frontend/app.js")

    assert response.status_code == 200
    assert "renderAuthPage" in response.text
    assert "renderProfilePage" in response.text
    assert "showProfile" in response.text
    assert "showPrivateView" in response.text


@pytest.mark.asyncio
async def test_frontend_serves_auth_feature_module(test_client: AsyncClient):
    response = await test_client.get("/frontend/features/auth/config.js")

    assert response.status_code == 200
    assert "AUTH_ENDPOINTS" in response.text
    assert "'/user/login'" in response.text
    assert "'/user/registration'" in response.text


@pytest.mark.asyncio
async def test_frontend_serves_profile_feature_module(test_client: AsyncClient):
    response = await test_client.get("/frontend/features/profile/controller.js")

    assert response.status_code == 200
    assert "'/user/me'" in response.text
    assert "/user/update/" in response.text
    assert "updateProfile" in response.text


@pytest.mark.asyncio
async def test_auth_path_removed_from_frontend_routes(test_client: AsyncClient):
    response = await test_client.get("/auth", follow_redirects=False)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_profile_path_redirects_to_frontend_profile_section(
    test_client: AsyncClient,
):
    response = await test_client.get("/profile", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/frontend/#profile"
