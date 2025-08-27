#!/usr/bin/env python3
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from eduschedule.adapters.sql.engine import session_scope
from eduschedule.adapters.sql.models.employee import Employee

def main() -> None:
    with session_scope() as s:
        rows = s.scalars(select(Employee).options(selectinload(Employee.role)).order_by(Employee.id))
        count = 0
        for i in rows:
            count += 1
            roleName = i.role.name if i.role else "-"
            active = 'yes' if i.active else 'no'
            print(f'{i.id:>3} {i.name:<20} {i.email:<30} role: {roleName} active: {active}')
        if count == 0:
            print('(no employees found)')

if __name__ == "__main__":
    main()