# Atelier Commerce API Reference

This guide documents the locally hosted API, its request payloads, response shapes, authentication requirements, and expected errors. It is written as a standalone reference for training and walkthroughs.

## Connection details

- Base URL: `http://127.0.0.1:8000`
- API prefix: `/api/v1`
- OpenAPI JSON: `GET /openapi.json`
- Interactive Swagger UI: `/docs`
- ReDoc: `/redoc`
- Content type for JSON request bodies: `application/json`
- Protected routes require `Authorization: Bearer <access_token>`.

Example authorization header:

```http
Authorization: Bearer eyJ...your-access-token
```

Successful protected responses never include a password hash. Reset tokens are not returned in API responses. The local password-reset mock prints a reset token to the server terminal.

## Response conventions

Errors generally use this shape:

```json
{ "detail": "Access denied" }
```

Request validation errors return HTTP `422` with FastAPI's field-level error details. A generic unexpected server error returns HTTP `500` with:

```json
{ "detail": "Internal server error" }
```

## Authentication

### `POST /api/v1/auth/signup`

Create a customer account. Public; no bearer token required.

Request:

```json
{
  "name": "Taylor Morgan",
  "email": "taylor@example.com",
  "password": "StrongPass123!"
}
```

Response `201 Created` (`Customer`):

```json
{
  "id": 4,
  "name": "Taylor Morgan",
  "email": "taylor@example.com",
  "created_at": "2026-10-15T10:30:00Z"
}
```

Errors: `409` if the email is already registered; `422` for invalid fields.

### `POST /api/v1/auth/login`

Authenticate with an email and password. Public.

Request:

```json
{ "email": "alice@example.com", "password": "Password123!" }
```

Response `200 OK` (`Token`):

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Errors: `401` for invalid credentials; `422` for invalid fields.

### `POST /api/v1/auth/logout`

Revoke the current token. Requires a valid bearer token. Repeating logout while the token remains valid returns `200` without adding a duplicate revocation.

Request body: none.

Response `200 OK`:

```json
{ "message": "Logged out" }
```

Errors: `401` if the token is missing, invalid, expired, or already revoked.

### `POST /api/v1/auth/refresh`

Rotate the current access token. Requires a valid bearer token. The old token is revoked as part of the rotation.

Request body: none.

Response `200 OK`: same shape as the login token response.

Errors: `401` if the token is missing, invalid, expired, or revoked.

### `POST /api/v1/auth/forgot-password`

Request a password reset. Public. The response is intentionally the same whether or not the email is registered.

Request:

```json
{ "email": "alice@example.com" }
```

Response `200 OK`:

```json
{ "message": "If the account exists, reset instructions have been issued" }
```

For this local mock, a reset token is printed to the server terminal. It is not included in the response body.

### `POST /api/v1/auth/reset-password`

Use a valid, unexpired, unused reset token. A successful reset consumes the token.

Request:

```json
{
  "token": "paste-the-one-time-token-from-the-server-terminal",
  "new_password": "AnotherStrongPass123!"
}
```

Response `200 OK`:

```json
{ "message": "Password updated" }
```

Errors: `400` for an unknown, expired, or already-used token; `422` for invalid fields.

### `GET /api/v1/auth/me`

Return the authenticated customer. Requires a bearer token.

Response `200 OK`: `Customer` shape, as shown for signup.

Errors: `401` if the token is missing, invalid, expired, or revoked.

## Customers

All customer routes below require a bearer token.

### `GET /api/v1/customers/me`

Return the current customer's profile.

Response `200 OK`: `Customer` shape.

### `PATCH /api/v1/customers/me`

Update the current customer's name. Only `name` is editable.

Request:

```json
{ "name": "Alice Morgan-Smith" }
```

Response `200 OK`: updated `Customer` shape.

Errors: `401` for missing or invalid authentication; `422` for invalid fields.

### `GET /api/v1/customers/{customer_id}`

Read a customer profile by numeric ID. A customer can read only their own profile.

Example: `GET /api/v1/customers/1`

Response `200 OK`: `Customer` shape.

Errors: `401` if unauthenticated; `403` if the requested ID belongs to another customer; `422` if the ID is not an integer.

### `GET /api/v1/customers/me/addresses`

List the authenticated customer's addresses.

Response `200 OK`:

```json
[
  {
    "id": 1,
    "customer_id": 1,
    "label": "Home",
    "line1": "12 Linking Road",
    "line2": null,
    "city": "Mumbai",
    "region": "Maharashtra",
    "postal_code": "400050",
    "country": "India",
    "is_default": true
  }
]
```

### `POST /api/v1/customers/me/addresses`

Add an address owned by the authenticated customer.

Request:

```json
{
  "label": "Work",
  "line1": "50 Linking Road",
  "line2": "Suite 8",
  "city": "Mumbai",
  "region": "Maharashtra",
  "postal_code": "400050",
  "country": "India",
  "is_default": false
}
```

Response `201 Created`: one address object, including generated `id` and `customer_id`.

Errors: `401` if unauthenticated; `422` for invalid fields.

### `PATCH /api/v1/customers/me/addresses/{address_id}`

Update an address owned by the authenticated customer. Any subset of address fields may be sent.

Request example:

```json
{ "label": "Primary home", "is_default": true }
```

Response `200 OK`: updated address object.

Errors: `401` if unauthenticated; `403` if the address belongs to another customer; `404` if the address does not exist; `422` for invalid fields.

### `DELETE /api/v1/customers/me/addresses/{address_id}`

Delete an address owned by the authenticated customer.

Response: `204 No Content` (empty body).

Errors: `401` if unauthenticated; `403` if the address belongs to another customer; `404` if the address does not exist.

## Products

Product routes are public and do not require authentication.

### `GET /api/v1/products`

List products. All query parameters are optional.

| Parameter | Type | Rules |
| --- | --- | --- |
| `category` | string | Exact category match, case-insensitive |
| `q` | string | Searches product name and description; maximum 100 characters |
| `min_price` | number | Must be zero or greater |
| `max_price` | number | Must be zero or greater |
| `page` | integer | Defaults to `1`; minimum `1` |
| `page_size` | integer | Defaults to `12`; range `1`–`100` |

Example: `GET /api/v1/products?category=Acid%20Wash&q=orbit&min_price=700&max_price=1200&page=1&page_size=12`

Response `200 OK` (`Product[]`):

```json
[
  {
    "id": 1,
    "name": "Moon Orbit Acid Wash Tee",
    "description": "A relaxed heavyweight cotton tee with a washed charcoal finish and original orbit artwork.",
    "category": "Acid Wash",
    "price": 999.0,
    "stock": 24,
    "featured": true
  }
]
```

Errors: `422` for invalid pagination or price values, or when `min_price` is greater than `max_price`.

### `GET /api/v1/products/search?q={search_term}`

Search product names and descriptions. `q` is required and must contain 1–100 characters.

Example: `GET /api/v1/products/search?q=acid%20wash`

Response `200 OK`: `Product[]`.

Errors: `422` if `q` is missing or invalid.

### `GET /api/v1/products/featured`

List products marked as featured.

Response `200 OK`: `Product[]`.

### `GET /api/v1/products/{product_id}`

Read one product.

Example: `GET /api/v1/products/1`

Response `200 OK`: one `Product` object.

Errors: `404` if the product does not exist; `422` if the ID is invalid.

### `GET /api/v1/products/{product_id}/reviews`

List reviews for a product.

Response `200 OK` (`Review[]`):

```json
[
  {
    "id": 1,
    "customer_name": "Maya R.",
    "rating": 5,
    "title": "Great everyday fit",
    "body": "The fabric feels substantial and the relaxed cut is spot on.",
    "created_at": "2026-10-15T10:30:00Z"
  }
]
```

Errors: `404` if the product does not exist; `422` if the ID is invalid.

## Orders

All order routes require a bearer token. Each order operation checks that the order belongs to the authenticated customer. A client cannot set or edit the customer/owner, order total, item price, or payment status.

### `POST /api/v1/orders`

Create an order. Product prices are read from the catalog on the server and stock is checked and decremented.

Request:

```json
{
  "items": [
    { "product_id": 1, "quantity": 1 },
    { "product_id": 2, "quantity": 2 }
  ],
  "shipping_address": "12 Linking Road, Mumbai, Maharashtra 400050"
}
```

`items` must contain 1–30 entries; each quantity must be 1–50. The address must contain 5–400 characters.

Response `201 Created` (`Order`):

```json
{
  "id": 10,
  "customer_id": 1,
  "status": "pending",
  "payment_status": "authorized",
  "total": 2997.0,
  "created_at": "2026-10-15T10:30:00Z",
  "shipping_address": "12 Linking Road, Mumbai, Maharashtra 400050",
  "items": [
    {
      "product_id": 1,
      "product_name": "Moon Orbit Acid Wash Tee",
      "quantity": 1,
      "unit_price": 999.0
    },
    {
      "product_id": 2,
      "product_name": "Star Map Layered Tee",
      "quantity": 2,
      "unit_price": 999.0
    }
  ]
}
```

Errors: `401` if unauthenticated; `422` for invalid or unavailable products, insufficient stock, or invalid fields.

### `GET /api/v1/orders`

List only the authenticated customer's orders.

Response `200 OK`: `Order[]`.

### `GET /api/v1/orders/{order_id}`

Read an order owned by the authenticated customer.

Response `200 OK`: one `Order` object.

Errors: `401` if unauthenticated; `403` if the order belongs to someone else; `404` if it does not exist.

### `PATCH /api/v1/orders/{order_id}`

Change the shipping address of an owned order that is still `pending`.

Request:

```json
{ "shipping_address": "88 New Address, Portland, Oregon 97205" }
```

Response `200 OK`: updated `Order` object.

Errors: `401` if unauthenticated; `403` if the order belongs to someone else; `404` if it does not exist; `409` if it is not pending; `422` for an invalid body. Other fields such as `customer_id`, `total`, `payment_status`, `status`, and line item prices are not editable.

### `POST /api/v1/orders/{order_id}/cancel`

Cancel an owned `pending` order. This restores the ordered quantities to product stock and marks the order cancelled.

Request body: none.

Response `200 OK`: updated `Order` object (status `cancelled`).

Errors: `401` if unauthenticated; `403` if the order belongs to someone else; `404` if it does not exist; `409` if it is no longer pending, including a second cancellation attempt.

### `GET /api/v1/orders/{order_id}/tracking`

Get synthetic tracking events for an owned order.

Response `200 OK`:

```json
{
  "order_id": 2,
  "status": "shipped",
  "events": [
    { "status": "Order placed", "occurred_at": "2026-10-15T10:30:00+00:00" },
    { "status": "Package shipped", "occurred_at": "2026-10-15T10:30:00+00:00" }
  ]
}
```

Events depend on the current order status and are synthetic, not carrier scans.

Errors: `401` if unauthenticated; `403` if the order belongs to someone else; `404` if it does not exist.

## Seeded local accounts

The idempotent seed script creates Alice, Bob, and Carol, addresses, orders, products, and reviews. All three accounts use the password `Password123!`.

| Name | Email |
| --- | --- |
| Alice Morgan | `alice@example.com` |
| Bob Chen | `bob@example.com` |
| Carol Singh | `carol@example.com` |

On a clean database, Alice is customer `1`, Bob is customer `2`, Carol is customer `3`; the seeded products begin with IDs `1`–`18`. Order IDs are assigned in seed order and may increase as new orders are created.
