from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal
from app.models import Customer, Address, Product, Order, OrderItem, ProductReview
from app.security import hash_password

PRODUCTS = [
    ("Moon Orbit Acid Wash Tee","A relaxed heavyweight cotton tee with a washed charcoal finish and original orbit artwork.","Acid Wash",999,24,True),
    ("Star Map Layered Tee","A cream graphic tee layered over a soft black long sleeve.","Layered Tees",999,18,True),
    ("Sage Ringer Tee","Vintage-inspired ringer construction in washed sage cotton.","Ringer Tees",899,35,True),
    ("Night Shift Oversized Tee","A boxy everyday tee with dropped shoulders and a substantial hand feel.","Oversized Tees",799,8,False),
    ("After Hours Acid Wash Tee","Deep graphite wash with a subtle tonal chest illustration.","Acid Wash",1199,60,True),
    ("Archive Heavyweight Hoodie","A roomy brushed-fleece hoodie with clean utility details.","Hoodies",1699,20,False),
    ("Static Long Sleeve Tee","A soft washed long sleeve with a small original chest print.","Long Sleeves",999,42,False),
    ("Contrast Stitch Ringer Tee","A faded cotton ringer tee with dark contrast trim.","Ringer Tees",899,28,True),
    ("Orbit Graphic Long Sleeve","A heavyweight long sleeve with fine-line celestial artwork.","Long Sleeves",1299,14,True),
    ("Cloudline Layered Tee","A cream and charcoal two-layer tee for an easy oversized fit.","Layered Tees",999,25,False),
    ("Signal Washed Boxy Tee","A roomy acid-washed silhouette with a small abstract front graphic.","Acid Wash",1099,11,False),
    ("Midnight Essential Tee","A clean heavyweight half-sleeve tee in deep charcoal.","Half Sleeves",699,19,False),
    ("Distortion Acid Wash Tee","Soft charcoal wash, sturdy neckline, and a one-off graphic treatment.","Acid Wash",1199,30,True),
    ("Double Layer Long Sleeve","An easy layered fit with a cream body and dark sleeves.","Layered Tees",1399,50,False),
    ("Mono Print Vest","A relaxed cotton vest with a low-key tonal print.","Vests",899,16,False),
    ("Washed Graphite Hoodie","Heavy fleece, relaxed shoulders, and a small embroidered-look emblem.","Hoodies",1899,22,True),
    ("Ecru Ringer Tee","A warm ecru body with charcoal collar and sleeve bands.","Ringer Tees",899,45,False),
    ("Ghostline Long Sleeve","A washed charcoal long sleeve with a minimal geometric chest mark.","Long Sleeves",1299,27,False),
]
CUSTOMERS = [("Alice Morgan","alice@example.com"),("Bob Chen","bob@example.com"),("Carol Singh","carol@example.com")]
def seed(db:Session):
    customers=[]
    for name,email in CUSTOMERS:
        c=db.query(Customer).filter_by(email=email).first()
        if not c:
            c=Customer(name=name,email=email,password_hash=hash_password("Password123!"));db.add(c);db.flush()
        customers.append(c)
    addresses=[("12 Linking Road","Mumbai","Maharashtra","400050"),("88 MG Road","Bengaluru","Karnataka","560001"),("305 Hauz Khas Road","New Delhi","Delhi","110016")]
    for c,(line,city,region,postal) in zip(customers,addresses):
        address=db.query(Address).filter_by(customer_id=c.id).order_by(Address.id).first()
        if not address:
            address=Address(customer_id=c.id,label="Home",line1=line,city=city,region=region,postal_code=postal,country="India",is_default=True);db.add(address)
        else:
            address.line1=line;address.city=city;address.region=region;address.postal_code=postal;address.country="India";address.is_default=True
    customer_addresses={c.id:address for c,address in zip(customers,addresses)}
    existing_products=db.query(Product).order_by(Product.id).all()
    products=[]
    for index,(name,description,category,price,stock,featured) in enumerate(PRODUCTS):
        p=existing_products[index] if index<len(existing_products) else db.query(Product).filter_by(name=name).first()
        if not p:p=Product(name=name,description=description,category=category,price=price,stock=stock,featured=featured);db.add(p)
        else:p.name=name;p.description=description;p.category=category;p.price=price;p.stock=stock;p.featured=featured
        db.flush();products.append(p)
    review_copy=[
        ("Maya R.",5,"Great everyday fit","The fabric feels substantial and the relaxed cut is spot on."),
        ("Jordan L.",4,"Better in person","Good weight, clean stitching, and the color looks even better in daylight."),
        ("Aarav K.",5,"Already a favorite","Comfortable from the first wear. The small graphic is a nice detail."),
    ]
    for p in products:
        existing_reviews=db.query(ProductReview).filter_by(product_id=p.id).order_by(ProductReview.id).all()
        for slot,(customer_name,rating,title,body) in enumerate(review_copy):
            if slot<len(existing_reviews):review=existing_reviews[slot];review.customer_name=customer_name;review.rating=rating;review.title=title;review.body=body
            else:db.add(ProductReview(product_id=p.id,customer_name=customer_name,rating=rating,title=title,body=body))
    if not db.query(Order).first():
        for ci,c in enumerate(customers):
            for offset,status in enumerate(("pending","shipped","delivered")):
                p=products[(ci*3+offset)%len(products)];qty=1+(offset%2)
                order=Order(customer_id=c.id,status=status,payment_status="authorized" if status!="delivered" else "paid",total=round(p.price*qty,2),created_at=datetime.now(timezone.utc)-timedelta(days=offset+ci),shipping_address=f"{addresses[ci][0]}, {addresses[ci][1]}, {addresses[ci][2]} {addresses[ci][3]}")
                db.add(order);db.flush();db.add(OrderItem(order_id=order.id,product_id=p.id,product_name=p.name,quantity=qty,unit_price=p.price))
    # Keep the local sample order snapshots aligned with the mock catalog after reseeding.
    for order in db.query(Order).all():
        address=customer_addresses.get(order.customer_id)
        if address:
            order.shipping_address=f"{address[0]}, {address[1]}, {address[2]} {address[3]}"
        for item in order.items:
            product=db.get(Product,item.product_id)
            if product:
                item.product_name=product.name
                item.unit_price=product.price
        order.total=round(sum(item.quantity*item.unit_price for item in order.items),2)
    db.commit()
def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:seed(db)
    print("Seed complete. Demo accounts share password: Password123!")
if __name__=="__main__":main()
