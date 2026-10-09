import os
import time
import traceback

from sqlalchemy import inspect, or_, select, text

from .database import get_db
from .models import (
    ApiLog, AuditLog, Base, FraudLog, Role, User, UserRole,
)
from .rbac import ROLE_DESCRIPTIONS

NEW_TXN_COLUMNS = {
    "category": "VARCHAR(50) NOT NULL DEFAULT 'Other'",
    "location": "VARCHAR(100) NULL",
    "device_id": "VARCHAR(100) NULL",
    "fraud_status": "VARCHAR(20) NOT NULL DEFAULT 'clean'",
}

TXN_INDEXES = {
    "idx_txn_created_at": "created_at",
    "idx_txn_amount": "amount",
    "idx_txn_status": "status",
    "idx_txn_user_created": "user_id, created_at",
}

ENV_ROLE_USERS = {
    "admin": "RBAC_ADMINS",
    "support": "RBAC_SUPPORT",
    "readonly": "RBAC_READONLY",
}


def _wait_for_tables(bind, names, tries=30, delay=2) -> bool:
    """Django creates users/transactions when it migrates, so wait for them."""
    for _ in range(tries):
        have = set(inspect(bind).get_table_names())
        if all(n in have for n in names):
            return True
        print(f"[bootstrap] waiting for tables {names} (Django migrations)...")
        time.sleep(delay)
    return False


def run_bootstrap() -> None:
    gen = get_db()
    try:
        db = next(gen)
        bind = db.get_bind()

        # 1) new tables (safe to run every start)
        Base.metadata.create_all(
            bind=bind,
            tables=[
                Role.__table__, UserRole.__table__,
                AuditLog.__table__, FraudLog.__table__, ApiLog.__table__,
            ],
        )

        if not _wait_for_tables(bind, ["users", "transactions"]):
            print("[bootstrap] users/transactions tables not found, skipping column setup")
            return

        # 2) new transaction columns
        insp = inspect(bind)
        existing_cols = {c["name"] for c in insp.get_columns("transactions")}
        for name, ddl in NEW_TXN_COLUMNS.items():
            if name not in existing_cols:
                db.execute(text(f"ALTER TABLE transactions ADD COLUMN {name} {ddl}"))
                print(f"[bootstrap] added transactions.{name}")

        # 3) search indexes
        existing_idx = {i["name"] for i in insp.get_indexes("transactions")}
        for idx, cols in TXN_INDEXES.items():
            if idx not in existing_idx:
                db.execute(text(f"CREATE INDEX {idx} ON transactions ({cols})"))
                print(f"[bootstrap] created index {idx}")
        db.commit()

        # 4) seed the three roles
        for name, desc in ROLE_DESCRIPTIONS.items():
            if not db.scalar(select(Role).where(Role.name == name)):
                db.add(Role(name=name, description=desc))
        db.commit()

        # 5) give roles to users listed in .env (username or email)
        for role, var in ENV_ROLE_USERS.items():
            for ident in [x.strip() for x in os.getenv(var, "").split(",") if x.strip()]:
                user = db.scalar(
                    select(User).where(or_(User.username == ident, User.email == ident))
                )
                if user is None:
                    print(f"[bootstrap] {var}: user '{ident}' not found yet")
                    continue
                row = db.get(UserRole, user.id)
                if row is None:
                    db.add(UserRole(user_id=user.id, role=role))
                else:
                    row.role = role
                print(f"[bootstrap] {ident} -> {role}")
        db.commit()
    except Exception:  # noqa: BLE001
        traceback.print_exc()
    finally:
        gen.close()