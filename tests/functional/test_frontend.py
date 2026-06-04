import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_frontend_index_contains_application_mount(test_client: AsyncClient):
    response = await test_client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="auth-app"' in response.text
    assert 'type="module" src="./app.js"' in response.text


@pytest.mark.asyncio
async def test_frontend_serves_vanilla_js_app(test_client: AsyncClient):
    response = await test_client.get("/frontend/app.js")

    assert response.status_code == 200
    assert "const API_ENDPOINTS" in response.text
    assert "'/user/login'" in response.text
    assert "'/user/registration'" in response.text
    assert "localStorage.setItem('access_token'" in response.text


@pytest.mark.asyncio
async def test_auth_path_redirects_to_frontend_auth_section(test_client: AsyncClient):
    response = await test_client.get("/auth", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/frontend/#auth"
