from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    masked_number: Mapped[str] = mapped_column(String(19))
    expiry_month: Mapped[int]
    expiry_year: Mapped[int]
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True)
    user_id: Mapped[int]
    card_id: Mapped[int | None]
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    description: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(10), default="PENDING")
    failure_reason: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]