#!/usr/bin/env python3
from __future__ import annotations
from sqlalchemy import select, func
from eduschedule.adapters.sql.engine import session_scope
from eduschedule.adapters.sql.models.employee import Role, Employee

def main() -> None:
    with session_scope() as s:
        results = s.execute(select(Role.id, Role.name, func.count(Employee.id)).select_from(Role)
                  .join(Employee, Employee.role_id == Role.id, isouter=True).group_by(Role.id, Role.name).order_by(Role.name)
                  ).all()
        
        if not results:
            print("(no roles found)")
            return
        
        for rid, name, n in results:
            print(f'{rid:>3} {name:<20} employees: {n}')

if __name__ == "__main__":
    main()