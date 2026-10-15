from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from app.config import settings

client = MongoClient(settings.mongodb_uri)
database: Database = client.get_default_database(settings.mongodb_database or "atelier_commerce")

def get_db():
    yield database

def init_db() -> None:
    database.customers.create_index("email", unique=True)
    database.products.create_index([("category", 1), ("name", 1)])
    database.orders.create_index("customer_id")
    database.revoked_tokens.create_index("jti", unique=True)
    database.password_reset_tokens.create_index("token_hash", unique=True)
    database.api_request_logs.create_index([("method", 1), ("endpoint", 1), ("requested_at", 1)])
    database.api_endpoint_stats.create_index([("method", 1), ("endpoint", 1)], unique=True)

def next_id(collection: Collection) -> int:
    from pymongo import ReturnDocument
    counter = collection.database.counters.find_one_and_update(
        {"_id": collection.name},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return counter["value"]
