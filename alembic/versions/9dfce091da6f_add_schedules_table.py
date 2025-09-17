"""add schedules table

Revision ID: 9dfce091da6f
Revises: 44ae8f802d44
Create Date: 2024-11-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9dfce091da6f"
down_revision: Union[str, Sequence[str], None] = "44ae8f802d44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("start_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_utc", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name=op.f("fk_schedules_employee_id_employees"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("end_utc > start_utc", name=op.f("ck_schedules_time_order")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_schedules")),
    )
    op.create_index(
        "ix_sched_emp_start_end",
        "schedules",
        ["employee_id", "start_utc", "end_utc"],
        unique=False,
    )
    op.create_index(op.f("ix_schedules_employee_id"), "schedules", ["employee_id"], unique=False)
    op.create_index(op.f("ix_schedules_start_utc"), "schedules", ["start_utc"], unique=False)
    op.create_index(op.f("ix_schedules_end_utc"), "schedules", ["end_utc"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_schedules_end_utc"), table_name="schedules")
    op.drop_index(op.f("ix_schedules_start_utc"), table_name="schedules")
    op.drop_index(op.f("ix_schedules_employee_id"), table_name="schedules")
    op.drop_index("ix_sched_emp_start_end", table_name="schedules")
    op.drop_table("schedules")
