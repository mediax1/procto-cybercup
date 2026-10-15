import sqlite3
from pathlib import Path
from app.database import database, init_db

SOURCE = Path(__file__).resolve().parents[1] / "commerce.db"

def read_rows(connection, table):
    return [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]

def migrate():
    if not SOURCE.exists():
        raise FileNotFoundError(f"SQLite source not found: {SOURCE}")
    init_db()
    connection = sqlite3.connect(SOURCE)
    connection.row_factory = sqlite3.Row
    try:
        customers = read_rows(connection, "customers")
        addresses = read_rows(connection, "addresses")
        products = read_rows(connection, "products")
        reviews = read_rows(connection, "product_reviews")
        orders = read_rows(connection, "orders")
        items = read_rows(connection, "order_items")
        customers_by_id = {row["id"]: row for row in customers}
        products_by_id = {row["id"]: row for row in products}
        for row in addresses:
            address = {key: row[key] for key in ("id", "label", "line1", "line2", "city", "region", "postal_code", "country", "is_default")}
            customers_by_id[row["customer_id"]].setdefault("addresses", []).append(address)
        for row in reviews:
            review = {key: row[key] for key in ("id", "customer_name", "rating", "title", "body", "created_at")}
            products_by_id[row["product_id"]].setdefault("reviews", []).append(review)
        for row in items:
            item = {key: row[key] for key in ("product_id", "product_name", "quantity", "unit_price")}
            orders_by_id = {order["id"]: order for order in orders}
            orders_by_id[row["order_id"]].setdefault("items", []).append(item)
        for collection_name, records in (("customers", customers), ("products", products), ("orders", orders)):
            collection = database[collection_name]
            for record in records:
                collection.replace_one({"id": record["id"]}, record, upsert=True)
            if records:
                database.counters.update_one({"_id": collection_name}, {"$max": {"value": max(record["id"] for record in records)}}, upsert=True)
        for table, collection_name, key in (
            ("revoked_tokens", "revoked_tokens", "id"),
            ("password_reset_tokens", "password_reset_tokens", "id"),
            ("api_request_logs", "api_request_logs", "id"),
            ("api_endpoint_stats", "api_endpoint_stats", "id"),
        ):
            for record in read_rows(connection, table):
                database[collection_name].replace_one({key: record[key]}, record, upsert=True)
    finally:
        connection.close()
    print("SQLite records copied to MongoDB.")

if __name__ == "__main__":
    migrate()

