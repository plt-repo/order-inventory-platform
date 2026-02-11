import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from project.db.models.users import User


@pytest.mark.anyio
async def test_health(client: AsyncClient, fastapi_app: FastAPI) -> None:
    """
    Checks the health endpoint.

    :param client: client for the app.
    :param fastapi_app: current FastAPI application.
    """
    url = fastapi_app.url_path_for("health_check")
    response = await client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.anyio
async def test_get_token(
        client: AsyncClient,
        fastapi_app: FastAPI,
        test_user: User
) -> None:
    login_url = fastapi_app.url_path_for("auth:jwt.login")
    login_data = {
        "username": "test@example.com",
        "password": "test_password",
    }
    login_response = await client.post(login_url, data=login_data)
    assert login_response.status_code == status.HTTP_200_OK
    token = login_response.json()["access_token"]
    assert token is not None
