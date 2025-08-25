from decimal import Decimal

from app.db.base_class import Base
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    isrc: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    album: Mapped[str | None] = mapped_column(String(150))
    artist: Mapped[str | None] = mapped_column(String(150))
    title: Mapped[str | None] = mapped_column(String(150))
    payout_per_play: Mapped[Decimal] = mapped_column(Numeric(precision=9, scale=8))
    licensing_group: Mapped[str | None] = mapped_column(String(150))
