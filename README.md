# Atelier Commerce API

A locally runnable commerce storefront and REST API built with FastAPI, PyMongo, MongoDB, Pydantic 2, and a responsive static interface.

## Requirements

- Python 3.11 or newer
- A MongoDB server or MongoDB Atlas database
- Windows PowerShell

## Setup and run

From the repository root:

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
Copy-Item .env.example .env
```

Set `MONGODB_URI` in `.env` to your MongoDB connection URI. If the URI contains a database name, the app uses it; otherwise it uses `MONGODB_DATABASE` or `atelier_commerce`.

```powershell
python -m pip install -r requirements.txt
python -m scripts.seed_data
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` for the storefront. Choose **API Guide** in the top navigation to read the complete store API reference on the site. Swagger is at `http://127.0.0.1:8000/docs`, ReDoc at `http://127.0.0.1:8000/redoc`, and OpenAPI JSON at `http://127.0.0.1:8000/openapi.json`. The same reference is available as [API_REFERENCE.md](API_REFERENCE.md).

To copy records from the previous local SQLite database into MongoDB, set `MONGODB_URI` and run:

```powershell
python -m scripts.migrate_sqlite_to_mongo
```

The migration reads `commerce.db` and upserts its records into MongoDB. It leaves the SQLite file in place.

## Test accounts

All seeded customer accounts use `Password123!`.

| Customer | Email |
| --- | --- |
| Alice Morgan | `alice@example.com` |
| Bob Chen | `bob@example.com` |
| Carol Singh | `carol@example.com` |

The seed script is idempotent. It creates three customers with addresses and three orders apiece, 18 products in four categories, and product reviews.

## Using the storefront

1. Start the server and open `http://127.0.0.1:8000/`.
2. Choose a quick sign-in, or use Alice’s account from the account table.
3. Browse, search, filter, and open a product to inspect its reviews.
4. Sign in and use Products, Orders, and Profile to explore the customer experience.
5. Open `/docs` when you want to inspect the API independently.

## API groups

The OpenAPI document contains exactly four tags: Customers, Authentication, Orders, and Products.

- `POST /api/v1/auth/signup`, `/login`, `/logout`, `/refresh`, `/forgot-password`, `/reset-password`; `GET /api/v1/auth/me`
- `GET/PATCH /api/v1/customers/me`; `GET /api/v1/customers/{customer_id}`; list/create/update/delete own addresses under `/api/v1/customers/me/addresses`
- `POST/GET /api/v1/orders`; `GET/PATCH /api/v1/orders/{order_id}`; `POST /api/v1/orders/{order_id}/cancel`; `GET /api/v1/orders/{order_id}/tracking`
- Public `GET /api/v1/products`, `/search`, `/featured`, `/{product_id}`, and `/{product_id}/reviews`

Order ownership is checked on each read, update, cancellation, and tracking request. Owner, amount, line item pricing, and payment state are not accepted as editable order fields. Password reset tokens are printed to the server terminal for this local mock flow and are never returned by the API.

## Isolated security lab route

The intentionally unsafe route is excluded from OpenAPI and is disabled by default. Enable it only for local scanner exercises by setting `LAB_VULNERABILITIES_ENABLED=true` in `.env`; `HOST` must remain `127.0.0.1` or `localhost`. The app refuses to import with the setting enabled and a non-loopback `HOST`. The route is `/api/lab/orders/{order_id}` and is not used by the interface.

## Configuration

Copy `.env.example` to `.env`, set `MONGODB_URI` to your MongoDB connection URI, and set a unique `SECRET_KEY` for persistent use. The documented server command binds only to `127.0.0.1:8000`.
