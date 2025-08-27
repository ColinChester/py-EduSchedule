import os
import subprocess
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from eduschedule.adapters.sql.base import Base

# Creates temp sqlite db for testing, builds tables tirectly from orm models (no alembic)
@pytest.fixture(scope="session")
def unitEngine(tmp_path_factory):
    dbFile = tmp_path_factory.mktemp("db") / "unit.db"
    eng = create_engine(f'sqlite:///{dbFile}', future=True)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()

# Cleanses temp db after test
@pytest.fixture()
def session(unitEngine):
    localSession = sessionmaker(unitEngine, autoflush=False, autocommit=False, future=True)
    s = localSession()
    try:
        yield s
        s.rollback()
    finally:
        s.close()

# Creates temp sqlite db, runs 'alembic upgrade head' with temp url and returns sqlalchemy url
@pytest.fixture(scope="session")
def tempDbUrl(tmp_path_factory):
    dbFile = tmp_path_factory.mktemp("db") / "alembic.db"
    url = f'sqlite:///{dbFile}'
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=env)
    return url

# Sets (runtime) DATABASE_URL to url of temp db
@pytest.fixture()
def cliEnv(tempDbUrl, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", tempDbUrl)
    return os.environ.copy()