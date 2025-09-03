import os
import subprocess
import alembic
import pytest
import pkgutil
from pathlib import Path
import importlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from eduschedule.adapters.sql.base import Base
from alembic import command
from alembic.config import Config

def _importModels() -> None:
    import eduschedule.adapters.sql.models as models
    for _f, modname, ispkg in pkgutil.iter_modules(models.__path__):
        if not modname.startswith("_"):
            importlib.import_module(f'{models.__name__}.{modname}')


# Creates temp sqlite db for testing, builds tables tirectly from orm models (no alembic)
@pytest.fixture(scope="session")
def unitEngine(tmp_path_factory):
    _importModels()
    dbFile = tmp_path_factory.mktemp("db") / "unit.db"
    eng = create_engine(f"sqlite:///{dbFile}", future=True)
    from eduschedule.adapters.sql.base import Base
    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        eng.dispose()


# Cleanses temp db after test
@pytest.fixture()
def session(unitEngine):
    localSession = sessionmaker(
        unitEngine, autoflush=False, autocommit=False, future=True
    )
    s = localSession()
    try:
        yield s
        s.rollback()
    finally:
        s.close()


# Creates temp sqlite db, runs 'alembic upgrade head' with temp url and returns sqlalchemy url
@pytest.fixture(scope="session")
def tempDbUrl(tmp_path_factory) -> str:
    _importModels()

    dbFile = tmp_path_factory.mktemp("db") / "alembic.db"
    url = f"sqlite:///{dbFile}"
    root = Path(__file__).resolve().parents[1]

    alembicIni = root / "alembic.ini"
    conf = Config(str(alembicIni))
    conf.set_main_option("script_location", str(root / "alembic"))
    conf.set_main_option("sqlalchemy.url", url)
    os.environ.setdefault("DATABASE_URL", url)
    command.upgrade(conf, "head")
    return url


# Sets (runtime) DATABASE_URL to url of temp db
@pytest.fixture()
def cliEnv(tempDbUrl, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", tempDbUrl)
    return os.environ.copy()
