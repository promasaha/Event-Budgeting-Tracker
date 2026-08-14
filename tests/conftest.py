import psycopg2
import pytest
from psycopg2 import errors as pg_errors
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

TEST_DB_NAME = f"{settings.db_name}_test"


def _admin_url(db_name: str) -> str:
    return (
        f"postgresql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{db_name}"
    )


@pytest.fixture(scope="session", autouse=True)
def _create_test_database():
    """Create a dedicated `<db>_test` database on the same Postgres server so
    tests never touch your dev data, then drop it afterwards."""
    conn = psycopg2.connect(_admin_url(settings.db_name))
    conn.autocommit = True
    with conn.cursor() as cur:
        try:
            cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
        except pg_errors.DuplicateDatabase:
            pass
    conn.close()

    yield

    conn = psycopg2.connect(_admin_url(settings.db_name))
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            f"WHERE datname = '{TEST_DB_NAME}' AND pid <> pg_backend_pid()"
        )
        cur.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
    conn.close()


@pytest.fixture(scope="session")
def engine(_create_test_database):
    eng = create_engine(_admin_url(TEST_DB_NAME))
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    """One connection + transaction per test, rolled back afterwards so tests
    never leak state into each other."""
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    from fastapi.testclient import TestClient

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-API-Key": settings.api_key}) as test_client:
        yield test_client
    app.dependency_overrides.clear()
