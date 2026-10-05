# Credit Card Payment System

A full stack fintech-style assignment: users register, save cards (masked only), make **simulated** payments, and view filtered transaction history. Admins can review users, cards and transactions, see a daily payment summary, and export transactions to CSV.

> No real payment gateway is used. CVVs and full card numbers are never stored.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite), served by nginx in Docker |
| Auth, Cards, Transactions, Admin | Django + Django REST Framework, JWT (SimpleJWT with token blacklist) |
| Payments | FastAPI (simulated gateway) |
| Database | MySQL 8 |
| Deployment | Docker + docker-compose |

## Project Structure

```
credit-card-payment-system/
├── django_service/     # Auth, cards, transactions, admin API (+ unit tests)
├── fastapi_service/    # Payment processing service
├── frontend/           # React app
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
| FastAPI payments | http://localhost:8001/docs |
| MySQL (host port) | localhost:3307 |

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
| `<Dk>` | `<Dinesh@2004>` |

## customer Credentials (for review)

| Username | Password |
|---|---|
| `<Levix>` | `<Levi@123>` |


## Security

- Passwords stored as **PBKDF2-SHA256** hashes (Django default).
- **JWT** access and refresh tokens; refresh tokens are **blacklisted on logout**.
- **No CVV storage**: the `cards` table has no CVV column.
- Only the **masked number and last 4 digits** are stored.
- Input validation through DRF serializers and Pydantic models (FastAPI), including filter validation (invalid filters return 400).
- SQL injection protection through the Django ORM and parameterized queries.
- Users can only pay with, and view, their own cards and transactions.
- Admin endpoints require a staff account; CSV exports are recorded in `admin_logs`.

## API Documentation

Swagger UI:

- Django API (auth, cards, transactions, admin) and FastAPI (payments) are both selectable at `http://localhost:8001/docs`.
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
| GET | `/api/admin/users/` | Admin: list users |
| GET | `/api/admin/cards/` | Admin: list cards |
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

An unknown or foreign card returns **404 Card not found**.

## Database Schema

Database: `payment_db` (MySQL)

**users** (Django auth user): `id`, `username`, `email`, `password` (hashed), `is_staff`, `date_joined`

**cards**: `id`, `user_id`, `card_holder`, `brand`, `masked_number`, `last4`, `expiry_month`, `expiry_year`

**transactions**: `id`, `reference`, `user_id`, `card_id`, `amount`, `currency`, `status` (PENDING, SUCCESS, FAILED), `description`, `failure_reason`, `created_at`

**admin_logs**: `id`, `admin_id`, `action`, `created_at`

Relationships: a user has many cards and many transactions; each transaction belongs to one card; admin logs reference the admin user.


## Author

Dineshkumar S, Python Full Stack Developer
