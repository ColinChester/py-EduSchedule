from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from eduschedule.config import DATABASE_URL

ENGINE = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
localSession = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)

@contextmanager
def session_scope():
    s = localSession()
    try:
        yield s
        s.commit()
    except:
        raise
    finally:
        s.close()