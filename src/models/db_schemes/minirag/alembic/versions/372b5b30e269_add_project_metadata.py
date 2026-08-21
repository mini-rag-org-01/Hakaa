"""add project metadata

Revision ID: 372b5b30e269
Revises: a3413f817c66
Create Date: 2026-08-21 00:50:21.799678

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "372b5b30e269"
down_revision: Union[str, None] = "a3413f817c66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column(
            "project_name",
            sa.String(length=150),
            nullable=True,
        ),
    )

    op.add_column(
        "projects",
        sa.Column(
            "project_description",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "projects",
        sa.Column(
            "is_public",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )

    op.add_column(
        "projects",
        sa.Column(
            "project_status",
            sa.String(length=20),
            server_default="draft",
            nullable=False,
        ),
    )

    op.create_index(
        op.f("ix_projects_is_public"),
        "projects",
        ["is_public"],
        unique=False,
    )

    op.create_index(
        op.f("ix_projects_project_status"),
        "projects",
        ["project_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_projects_project_status"),
        table_name="projects",
    )

    op.drop_index(
        op.f("ix_projects_is_public"),
        table_name="projects",
    )

    op.drop_column("projects", "project_status")
    op.drop_column("projects", "is_public")
    op.drop_column("projects", "project_description")
    op.drop_column("projects", "project_name")