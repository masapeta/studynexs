"""School-scoped mobile and username uniqueness.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("users_mobile_key", "users", type_="unique")
    op.drop_constraint("users_username_key", "users", type_="unique")
    op.create_unique_constraint("uq_users_school_mobile", "users", ["school_id", "mobile"])
    op.create_unique_constraint("uq_users_school_username", "users", ["school_id", "username"])


def downgrade() -> None:
    op.drop_constraint("uq_users_school_username", "users", type_="unique")
    op.drop_constraint("uq_users_school_mobile", "users", type_="unique")
    op.create_unique_constraint("users_username_key", "users", ["username"])
    op.create_unique_constraint("users_mobile_key", "users", ["mobile"])
