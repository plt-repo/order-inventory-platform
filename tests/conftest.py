from logging import getLogger
from typing import Any, AsyncGenerator, Callable, List

import pytest
from fastapi import FastAPI
from fastapi_users.password import PasswordHelper
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from project.db.dependencies import get_db_session
from project.db.models.users import User, get_jwt_strategy
from project.db.repositories.user import UserRepository
from project.db.utils import create_database, drop_database
from project.settings import settings
from project.web.application import get_app

logger = getLogger(__name__)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Backend for anyio pytest plugin.

    :return: backend name.
    """
    return "asyncio"


@pytest.fixture(scope="session")
async def _engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create engine and databases.

    :yield: new engine.
    """
    from project.db.meta import meta
    from project.db.models import load_all_models

    load_all_models()

    await create_database()

    engine = create_async_engine(str(settings.db_url))
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()
        await drop_database()


@pytest.fixture
async def session_factory(
        _engine: AsyncEngine,
) -> AsyncGenerator[Callable[[], AsyncSession], None]:
    """
    Фикстура, создающая независимые сессии по требованию.
    Каждый вызов создает новую сессию с собственной транзакцией.
    """
    active_sessions: List[AsyncSession] = []

    session_maker = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
    )

    def create_session() -> AsyncSession:
        session = session_maker()
        active_sessions.append(session)
        return session

    yield create_session

    for session in active_sessions:
        try:
            if session.in_transaction():
                await session.rollback()
            await session.close()
        except Exception:
            pass


@pytest.fixture
async def dbsession(
        _engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get session to database.

    Fixture that returns a SQLAlchemy session with a SAVEPOINT, and the rollback to it
    after the test completes.

    :param _engine: current engine.
    :yields: async session.
    """
    connection = await _engine.connect()
    trans = await connection.begin()
    logger.info("Соединение с базой данных установлено и начата транзакция.")

    session_maker = async_sessionmaker(
        connection,
        expire_on_commit=False,
    )
    session = session_maker()

    try:
        yield session
    finally:
        await session.close()
        if trans.is_active:
            await trans.rollback()
        logger.info("Транзакция откатана, соединение закрыто.")
        await connection.close()


@pytest.fixture
def fastapi_app(
        dbsession: AsyncSession,
) -> FastAPI:
    """
    Fixture for creating FastAPI app.

    :return: fastapi app with mocked dependencies.
    """
    application = get_app()
    application.dependency_overrides[get_db_session] = lambda: dbsession
    return application


@pytest.fixture
async def client(
        fastapi_app: FastAPI,
        anyio_backend: Any,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that creates client for requesting server.

    :param fastapi_app: the application.
    :yield: client for the app.
    """
    async with AsyncClient(app=fastapi_app, base_url="http://test", timeout=2.0) as ac:
        yield ac


@pytest.fixture
async def test_user(dbsession: AsyncSession) -> User:
    """Creates a test user."""
    password_helper = PasswordHelper()
    hashed_password = password_helper.hash("test_password")

    return (await UserRepository(dbsession).get_or_create(
        lookup={"email": "test@example.com"},
        defaults={
            "hashed_password": hashed_password,
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
        },
    ))[1]


@pytest.fixture
async def jwt_test_user(test_user: User) -> str:
    """ JWT  token for test_user"""
    strategy = get_jwt_strategy()
    token = await strategy.write_token(test_user)
    return token


@pytest.fixture
async def auth_client(
        jwt_test_user: str,
        fastapi_app: FastAPI,
        anyio_backend: Any,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that creates auth-client by test_user for requesting server.

    :param fastapi_app: the application.
    :param jwt_test_user: ...
    :param anyio_backend: ...
    :yield: client for the app.
    """
    headers = {"Authorization": f"Bearer {jwt_test_user}"}
    async with AsyncClient(app=fastapi_app, headers=headers, base_url="http://test", timeout=2.0) as ac:
        yield ac


@pytest.fixture
async def test_user(dbsession: AsyncSession) -> User:
    """Creates a test user."""
    password_helper = PasswordHelper()
    hashed_password = password_helper.hash("test_password")

    return (await UserRepository(dbsession).get_or_create(
        lookup={"email": "test@example.com"},
        defaults={
            "hashed_password": hashed_password,
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
        },
    ))[1]
