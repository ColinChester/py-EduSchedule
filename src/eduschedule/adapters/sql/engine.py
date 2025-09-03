from __future__ import annotations
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

def _dbUrl() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./eduschedule.db")

def _makeEngine():
    eng = create_engine(_dbUrl(), future=True)
    @event.listens_for(eng, "connect")
    def foreignKeyOn(dbapiConn, _):
        try:
            dbapiConn.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass
    return eng

@contextmanager
def session_scope():
    eng = _makeEngine()
    Session = sessionmaker(bind=eng, autoflush=False, autocommit=False, future=True)
    s = Session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
        eng.dispose()
