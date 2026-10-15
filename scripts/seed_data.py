from datetime import datetime, timezone, timedelta
from app.database import database, init_db
from app.security import hash_password

PRODUCTS = [
    ("Moon Orbit Acid Wash Tee", "A relaxed heavyweight cotton tee with a washed charcoal finish and original orbit artwork.", "Acid Wash", 999, 24, True),
    ("Star Map Layered Tee", "A cream graphic tee layered over a soft black long sleeve.", "Layered Tees", 999, 18, True),
    ("Sage Ringer Tee", "Vintage-inspired ringer construction in washed sage cotton.", "Ringer Tees", 899, 35, True),
    ("Night Shift Oversized Tee", "A boxy everyday tee with dropped shoulders and a substantial hand feel.", "Oversized Tees", 799, 8, False),
    ("After Hours Acid Wash Tee", "Deep graphite wash with a subtle tonal chest illustration.", "Acid Wash", 1199, 60, True),
    ("Archive Heavyweight Hoodie", "A roomy brushed-fleece hoodie with clean utility details.", "Hoodies", 1699, 20, False),
    ("Static Long Sleeve Tee", "A soft washed long sleeve with a small original chest print.", "Long Sleeves", 999, 42, False),
    ("Contrast Stitch Ringer Tee", "A faded cotton ringer tee with dark contrast trim.", "Ringer Tees", 899, 28, True),
    ("Orbit Graphic Long Sleeve", "A heavyweight long sleeve with fine-line celestial artwork.", "Long Sleeves", 1299, 14, True),
    ("Cloudline Layered Tee", "A cream and charcoal two-layer tee for an easy oversized fit.", "Layered Tees", 999, 25, False),
    ("Signal Washed Boxy Tee", "A roomy acid-washed silhouette with a small abstract front graphic.", "Acid Wash", 1099, 11, False),
    ("Midnight Essential Tee", "A clean heavyweight half-sleeve tee in deep charcoal.", "Half Sleeves", 699, 19, False),
    ("Distortion Acid Wash Tee", "Soft charcoal wash, sturdy neckline, and a one-off graphic treatment.", "Acid Wash", 1199, 30, True),
    ("Double Layer Long Sleeve", "An easy layered fit with a cream body and dark sleeves.", "Layered Tees", 1399, 50, False),
    ("Mono Print Vest", "A relaxed cotton vest with a low-key tonal print.", "Vests", 899, 16, False),
    ("Washed Graphite Hoodie", "Heavy fleece, relaxed shoulders, and a small embroidered-look emblem.", "Hoodies", 1899, 22, True),
    ("Ecru Ringer Tee", "A warm ecru body with charcoal collar and sleeve bands.", "Ringer Tees", 899, 45, False),
    ("Ghostline Long Sleeve", "A washed charcoal long sleeve with a minimal geometric chest mark.", "Long Sleeves", 1299, 27, False),
]
CUSTOMERS = [("Alice Morgan", "alice@example.com"), ("Bob Chen", "bob@example.com"), ("Carol Singh", "carol@example.com")]
ADDRESSES = [
    ("12 Linking Road", "Mumbai", "Maharashtra", "400050"),
    ("88 MG Road", "Bengaluru", "Karnataka", "560001"),
    ("305 Hauz Khas Road", "New Delhi", "Delhi", "110016"),
]
REVIEWS = [
    {"customer_name": "Maya R.", "rating": 5, "title": "Great everyday fit", "body": "The fabric feels substantial and the relaxed cut is spot on."},
    {"customer_name": "Jordan L.", "rating": 4, "title": "Better in person", "body": "Good weight, clean stitching, and the color looks even better in daylight."},
    {"customer_name": "Aarav K.", "rating": 5, "title": "Already a favorite", "body": "Comfortable from the first wear. The small graphic is a nice detail."},
]

def seed(db=database):
    customers = []
    for index, (name, email) in enumerate(CUSTOMERS, start=1):
        line, city, region, postal = ADDRESSES[index - 1]
        address = {"label": "Home", "line1": line, "line2": None, "city": city, "region": region, "postal_code": postal, "country": "India", "is_default": True}
        db.customers.update_one({"email": email}, {"$setOnInsert": {"id": index, "name": name, "email": email, "password_hash": hash_password("Password123!"), "created_at": datetime.now(timezone.utc)}, "$set": {"addresses": [address]}}, upsert=True)
        customers.append(db.customers.find_one({"email": email}))
    products = []
    for index, (name, description, category, price, stock, featured) in enumerate(PRODUCTS, start=1):
        product = {"id": index, "name": name, "description": description, "category": category, "price": price, "stock": stock, "featured": featured, "reviews": REVIEWS}
        db.products.update_one({"id": index}, {"$set": product}, upsert=True)
        products.append(product)
    if db.orders.count_documents({}) == 0:
        for customer_index, customer in enumerate(customers):
            line, city, region, postal = ADDRESSES[customer_index]
            for offset, status in enumerate(("pending", "shipped", "delivered")):
                product = products[(customer_index * 3 + offset) % len(products)]
                quantity = 1 + offset % 2
                item = {"product_id": product["id"], "product_name": product["name"], "quantity": quantity, "unit_price": product["price"]}
                db.orders.insert_one({"id": customer_index * 3 + offset + 1, "customer_id": customer["id"], "status": status, "payment_status": "authorized" if status != "delivered" else "paid", "total": round(product["price"] * quantity, 2), "created_at": datetime.now(timezone.utc) - timedelta(days=offset + customer_index), "shipping_address": f"{line}, {city}, {region} {postal}", "items": [item]})
    for collection in (db.customers, db.products, db.orders):
        maximum = collection.find_one(sort=[("id", -1)])
        if maximum:
            db.counters.update_one({"_id": collection.name}, {"$max": {"value": maximum["id"]}}, upsert=True)

def main():
    init_db()
    seed()
    print("Seed complete. Demo accounts share password: Password123!")

if __name__ == "__main__":
    main()

