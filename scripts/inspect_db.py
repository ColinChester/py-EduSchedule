from sqlalchemy import create_engine, inspect

eng = create_engine("sqlite:///./eduschedule.db", future=True)
insp = inspect(eng)

print("Tables", insp.get_table_names())
print("Employees columns:")
for c in insp.get_columns("employees"):
    print(c)