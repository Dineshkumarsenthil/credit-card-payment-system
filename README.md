# Credit Card Payment System

A full stack fintech-style assignment: users register, save cards (masked only), make **simulated** payments, view filtered transaction history, see a spending dashboard, and download monthly PDF statements. Admins can review users, cards and transactions, block or unblock cards, change credit limits, monitor card activity, see a daily payment summary, and export transactions to CSV.

> No real payment gateway is used. CVVs and full card numbers are never stored.

## Features

- **Auth:** register, login, refresh and logout with JWT (refresh tokens are blacklisted on logout).
- **Cards:** save and delete cards; only the masked number and last 4 digits are stored.
- **Payments:** simulated gateway (PENDING, then SUCCESS or FAILED); blocked cards are rejected.
- **Dashboard:** total spent, available credit, total transactions, monthly spending, 7-day chart and last 5 transactions (`GET /dashboard/summary`).
- **Email alerts:** sent when a payment is over the alert amount (default ₹5,000), when a card is blocked, and when available credit falls below 10%.
- **Dark mode:** light and dark themes with a sidebar toggle, built with React Context, responsive down to phone width.
- **Monthly statement PDF:** downloadable per month, with masked card details, summary and transaction list.
- **Admin card management:** view all cards, block and unblock, update credit limits, and view card activity. Every admin action is written to `admin_logs`.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite) with Tailwind CSS, served by nginx in Docker |
| Auth, Cards, Transactions, Admin, Statements | Django + Django REST Framework, JWT (SimpleJWT with token blacklist) |
| Payments and Dashboard summary | FastAPI (simulated gateway) |
| Database | MySQL 8 |
| Email (development) | Mailpit (catches all outgoing mail) |
| Deployment | Docker + docker-compose |

## Project Structure

```
credit-card-payment-system/
├── django_service/     # Auth, cards, transactions, admin API, statements (+ unit tests)
├── fastapi_service/    # Payment processing and dashboard summary service
├── frontend/           # React app (pages, components, theme)
├── db/                 # MySQL dump (dump.sql)
├── docker-compose.yml
├── .env.example
└── Credit_Card_Payment_System.postman_collection.json
```

## Setup

### Run with Docker (recommended)

```bash
git clone https://github.com/Dineshkumarsenthil/credit-card-payment-system.git
cd credit-card-payment-system
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Django API | http://localhost:8000/admin/ |
| Django API (Swagger) | http://localhost:8001/docs (select the Django spec) |
| FastAPI Payment API (Swagger) | http://localhost:8001/docs |
| Mailpit (email inbox) | http://localhost:8025 |
| MySQL (host port) | localhost:3307 |

### Environment variables

Set these in `.env` (see `.env.example` for the full list):

| Variable | Purpose |
|---|---|
| `EMAIL_*` | SMTP settings used for alerts (Mailpit in development) |
| `ALERT_AMOUNT` | Payment amount that triggers the large-payment email (default 5000) |
| `LOW_CREDIT_PERCENT` | Low-credit alert threshold in percent (default 10) |
| `PAYMENT_SUCCESS_RATE` | Chance a simulated payment succeeds (0 to 1; use 1 for demos) |

Alert emails go to the email address saved on the user account, so give your test user an email in Django admin.

### Load the database dump (optional)

```bash
mysql -u root -p payment_db < db/dump.sql
```

### Create an admin user

```bash
docker compose exec django python manage.py createsuperuser
```

### Run the tests

```bash
cd django_service
python manage.py test
# with coverage
coverage run manage.py test && coverage report
```

## Admin Credentials (for review)

| Username | Password |
|---|---|
| `Dk` | `Dinesh@2004` |

## Customer Credentials (for review)

| Username | Password |
|---|---|
| `Levix` | `Levi@123` |

## Security

- Passwords stored as **PBKDF2-SHA256** hashes (Django default).
- **JWT** access and refresh tokens; refresh tokens are **blacklisted on logout**.
- **No CVV storage**: the `cards` table has no CVV column.
- Only the **masked number and last 4 digits** are stored, and emails and statements show masked numbers only.
- Input validation through DRF serializers and Pydantic models (FastAPI), including filter validation (invalid filters return 400).
- SQL injection protection through the Django ORM and parameterized queries.
- Users can only pay with, and view, their own cards, transactions and statements.
- Blocked cards cannot be used for payments.
- Admin endpoints require a staff account (non-admin users get **403**).
- Admin actions (CSV export, block, unblock, limit changes) are recorded in `admin_logs`.

## API Documentation

Swagger UI:

- Django API (auth, cards, transactions, admin, statements) and FastAPI (payments, dashboard) are both selectable at `http://localhost:8001/docs`.
- A Postman collection is included: `Credit_Card_Payment_System.postman_collection.json`.

To authorize in Swagger, call `POST /api/auth/login/`, copy the `access` token, click **Authorize**, and paste it.

### Django endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register a user |
| POST | `/api/auth/login/` | Login, returns access and refresh tokens |
| POST | `/api/auth/refresh/` | Refresh the access token |
| POST | `/api/auth/logout/` | Blacklist the refresh token |
| GET | `/api/auth/me/` | Current user |
| GET | `/api/cards/` | List my saved cards |
| POST | `/api/cards/` | Add a card (stores masked number and last4) |
| DELETE | `/api/cards/{id}/` | Delete a card |
| GET | `/api/transactions/` | My transactions (filter by `status`, amount range, date range) |
| GET | `/api/statements/` | Download my monthly statement as a PDF |
| GET | `/api/admin/users/` | Admin: list users |
| GET | `/api/admin/cards/` | Admin: list all cards |
| POST | `/api/admin/cards/{id}/block/` | Admin: block a card (sends an email alert) |
| POST | `/api/admin/cards/{id}/unblock/` | Admin: unblock a card |
| PATCH | `/api/admin/cards/{id}/limit/` | Admin: update the credit limit |
| GET | `/api/admin/cards/{id}/activity/` | Admin: recent payments and admin actions for a card |
| GET | `/api/admin/transactions/` | Admin: list all transactions |
| GET | `/api/admin/transactions/export/` | Admin: CSV export (logged) |
| GET | `/api/admin/summary/` | Admin: daily payment summary |

### FastAPI endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |
| POST | `/payments` | Make a simulated payment (starts PENDING, ends SUCCESS or FAILED) |
| GET | `/payments` | List my payments |
| GET | `/payments/{reference}` | Get one payment |
| GET | `/dashboard/summary` | Dashboard totals and last 5 transactions (JWT required) |

An unknown or foreign card returns **404 Card not found**. A blocked card returns **403 This card is blocked**.

## Email Alerts

| Trigger | Email |
|---|---|
| Payment over the alert amount (₹5,000) | Payment alert with the masked card and reference |
| Card blocked by an admin | "Your card **** 1111 has been blocked" |
| Available credit below 10% of the limit | Low available credit alert |

In development, open Mailpit at http://localhost:8025 to see the emails.

## Database Schema

Database: `payment_db` (MySQL)

**users** (Django auth user): `id`, `username`, `email`, `password` (hashed), `is_staff`, `date_joined`

**cards**: `id`, `user_id`, `card_holder`, `brand`, `masked_number`, `last4`, `expiry_month`, `expiry_year`, `credit_limit`, `is_blocked`, `blocked_at`, `created_at`

**transactions**: `id`, `reference`, `user_id`, `card_id`, `amount`, `currency`, `status` (PENDING, SUCCESS, FAILED), `description`, `failure_reason`, `created_at`

**admin_logs**: `id`, `admin_id`, `action`, `created_at` (the action text includes the card id and masked number for card actions)

Relationships: a user has many cards and many transactions; each transaction belongs to one card; admin logs reference the admin user.

## Author

Dineshkumar S, Python Full Stack Developer
