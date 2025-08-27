from sqlalchemy import create_engine, inspect

def alembicDbCreateTest(tempDbUrl):
    eng = create_engine(tempDbUrl, future=True)
    insp = inspect(eng)
    tables = set(insp.get_table_names())
    assert {"roles", "employees"}.issubset(tables), tables