import json
import os
import random
import time
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user_id
from .database import get_db
from .models import Card, Transaction, utcnow

SUCCESS_RATE = float(os.getenv("PAYMENT_SUCCESS_RATE", "0.8"))
FAILURE_REASONS = [
    "Insufficient funds",
    "Card declined by issuer",
    "Suspected fraud",
    "Network timeout",
]
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

# Where the Django schema lives (drf-spectacular) and where this service runs
DJANGO_SCHEMA_URL = os.getenv("DJANGO_SCHEMA_URL", "http://127.0.0.1:8000/api/schema/")
FASTAPI_SCHEMA_URL = os.getenv("FASTAPI_SCHEMA_URL", "http://127.0.0.1:8001/openapi.json")

app = FastAPI(
    title="Payment System - Payment Service",
    version="1.0.0",
    # The default /docs page is replaced by the combined page defined below
    docs_url=None,
    description=(
        "Simulated payment gateway for the Credit Card Payment System.\n\n"
        "**Authentication:** log in through the Django service "
        "(`POST /api/auth/login/`), copy the `access` token and click "
        "**Authorize** here.\n\n"
        "**Security:** no real payment gateway is used, the CVV is never received "
        "or stored, and users can only pay with their own cards."
    ),
    openapi_tags=[
        {"name": "System", "description": "Service health"},
        {"name": "Payments", "description": "Create and list simulated payments"},
    ],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


SWAGGER_CDN = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5"


@app.get("/docs", include_in_schema=False)
def swagger_ui():
    """One Swagger page with a dropdown for both APIs (Django and FastAPI)."""
    urls = [
        {"url": DJANGO_SCHEMA_URL, "name": "Django - Auth, Cards, Transactions, Admin"},
        {"url": FASTAPI_SCHEMA_URL, "name": "FastAPI - Payments"},
    ]
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Payment System - API Docs</title>
  <link rel="stylesheet" href="{SWAGGER_CDN}/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="{SWAGGER_CDN}/swagger-ui-bundle.js"></script>
  <script src="{SWAGGER_CDN}/swagger-ui-standalone-preset.js"></script>
  <script>
    window.ui = SwaggerUIBundle({{
      urls: {json.dumps(urls)},
      "urls.primaryName": {json.dumps(urls[0]["name"])},
      dom_id: "#swagger-ui",
      deepLinking: true,
      persistAuthorization: true,
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
      plugins: [SwaggerUIBundle.plugins.DownloadUrl],
      layout: "StandaloneLayout"
    }});
  </script>
</body>
</html>"""
    return HTMLResponse(html)


class PaymentIn(BaseModel):
    card_id: int = Field(description="ID of one of your saved cards")
    amount: Decimal = Field(
        gt=0, le=1_000_000, max_digits=12, decimal_places=2,
        description="Amount to charge, up to 2 decimal places",
    )
    currency: str = Field(default="INR", pattern="^[A-Z]{3}$",
                          description="3-letter currency code")
    description: str = Field(default="", max_length=255)

    model_config = {
        "json_schema_extra": {
            "example": {
                "card_id": 1,
                "amount": "250.50",
                "currency": "INR",
                "description": "Order #1001",
            }
        }
    }


class PaymentOut(BaseModel):
    reference: str
    status: Literal["PENDING", "SUCCESS", "FAILED"]
    amount: Decimal
    currency: str
    failure_reason: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ErrorOut(BaseModel):
    detail: str


@app.get("/health", tags=["System"], summary="Health check")
def health():
    return {"status": "ok"}


@app.post(
    "/payments",
    response_model=PaymentOut,
    status_code=201,
    tags=["Payments"],
    summary="Make a simulated payment",
    description=(
        "Creates a PENDING transaction, simulates the gateway and stores the "
        "final SUCCESS or FAILED result. The card must belong to the logged-in user "
        "and must not be expired."
    ),
    responses={
        400: {"model": ErrorOut, "description": "Card has expired"},
        401: {"model": ErrorOut, "description": "Missing, invalid or expired token"},
        404: {"model": ErrorOut, "description": "Card not found for this user"},
        422: {"description": "Validation error (amount, currency, card_id)"},
    },
)
def make_payment(
    payload: PaymentIn,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # The card must belong to the logged-in user
    card = db.scalar(
        select(Card).where(Card.id == payload.card_id, Card.user_id == user_id)
    )
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    today = utcnow()
    if (card.expiry_year, card.expiry_month) < (today.year, today.month):
        raise HTTPException(status_code=400, detail="Card has expired")

    # 1) Create the transaction as PENDING
    now = utcnow()
    txn = Transaction(
        reference=uuid.uuid4().hex,
        user_id=user_id,
        card_id=card.id,
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
        status="PENDING",
        failure_reason="",
        created_at=now,
        updated_at=now,
    )
    db.add(txn)
    db.commit()

    # 2) Simulate the gateway (no real payment gateway is used)
    time.sleep(1)
    if random.random() < SUCCESS_RATE:
        txn.status = "SUCCESS"
    else:
        txn.status = "FAILED"
        txn.failure_reason = random.choice(FAILURE_REASONS)
    txn.updated_at = utcnow()
    db.commit()
    db.refresh(txn)
    return txn


@app.get(
    "/payments",
    response_model=list[PaymentOut],
    tags=["Payments"],
    summary="List my payments",
    description="Returns only the logged-in user's payments, newest first.",
    responses={401: {"model": ErrorOut, "description": "Unauthorized"}},
)
def list_payments(
    status: Literal["PENDING", "SUCCESS", "FAILED"] | None = Query(
        None, description="Filter by payment status"
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        stmt = stmt.where(Transaction.status == status)
    return db.scalars(stmt).all()


@app.get(
    "/payments/{reference}",
    response_model=PaymentOut,
    tags=["Payments"],
    summary="Get one payment",
    description="Returns the status of one of your payments by its reference.",
    responses={
        401: {"model": ErrorOut, "description": "Unauthorized"},
        404: {"model": ErrorOut, "description": "Payment not found for this user"},
    },
)
def get_payment(
    reference: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    txn = db.scalar(
        select(Transaction).where(
            Transaction.reference == reference, Transaction.user_id == user_id
        )
    )
    if txn is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return txn