"""checkin_fields_on_registration

Revision ID: e8c075066969
Revises: 80fd837094a4
Create Date: 2026-08-17 20:31:32.062362

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8c075066969'
down_revision: Union[str, Sequence[str], None] = '80fd837094a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # autogenerate روی این محیط دیف خالی داد چون DB dev محلی از قبل (حین
    # اشکال‌زدایی batch mode) این دو ستون رو گرفته بود — برای بقیه‌ی محیط‌ها
    # (Docker/DB تازه) دستی نوشته شده. بدون FK رسمی، نگاه کن به کامنت مدل.
    op.add_column("registrations", sa.Column("checked_in_at", sa.DateTime(), nullable=True))
    op.add_column("registrations", sa.Column("checked_in_by_user_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("registrations", "checked_in_by_user_id")
    op.drop_column("registrations", "checked_in_at")
