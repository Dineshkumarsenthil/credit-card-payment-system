from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Float, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    """Read-only mapping of the Django user table, used only to look up the email."""

    __tablename__ = "users"  # accounts.User uses db_table "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(254))


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    masked_number: Mapped[str] = mapped_column(String(19))
    expiry_month: Mapped[int]
    expiry_year: Mapped[int]
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)


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
    # --- new columns (added to the table automatically at startup) ---
    category: Mapped[str] = mapped_column(String(50), default="Other", server_default="Other")
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fraud_status: Mapped[str] = mapped_column(String(20), default="clean", server_default="clean")


# ---------------- RBAC ----------------
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    description: Mapped[str] = mapped_column(String(255), default="")


class UserRole(Base):
    """One staff role per user. Users without a row are normal customers."""

    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    role: Mapped[str] = mapped_column(String(30))


# ---------------- Logs ----------------
class AuditLog(Base):
    """Admin/staff actions: CARD_BLOCK, CARD_UNBLOCK, LIMIT_UPDATE, ROLE_ASSIGN."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(String(50))
    card_id: Mapped[int | None] = mapped_column(index=True, nullable=True)
    old_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class FraudLog(Base):
    __tablename__ = "fraud_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(index=True)
    user_id: Mapped[int]
    card_id: Mapped[int | None]
    rule_triggered: Mapped[str] = mapped_column(String(100))
    details: Mapped[str] = mapped_column(String(255), default="")
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class ApiLog(Base):
    __tablename__ = "api_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint: Mapped[str] = mapped_column(String(200))
    method: Mapped[str] = mapped_column(String(10))
    status_code: Mapped[int]
    response_time_ms: Mapped[float] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)