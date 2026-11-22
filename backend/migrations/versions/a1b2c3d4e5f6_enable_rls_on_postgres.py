"""enable row level security on postgres

Supabase exposes the public schema through its REST API. Enabling RLS with no policy closes
that path; the app connects as the table owner and is not affected. No-op on SQLite.

Revision ID: a1b2c3d4e5f6
Revises: 0e8780d59b76
Create Date: 2026-11-22 15:40:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "0e8780d59b76"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("teams", "players", "matches", "games", "alembic_version")


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
