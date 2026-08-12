from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class Instructor(Base, TimestampMixin):
    __tablename__ = "instructors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    bio: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linked_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
