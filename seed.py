# seed.py
from app import app, db, Product
from datetime import datetime

with app.app_context():
    # Create tables (safe to run multiple times)
    db.create_all()

    # Optional: clear old products
    Product.query.delete()

    products = [
        Product(
            name="Cold Pressed Coconut Oil",
            price=299.0,
            image="coconut.jpg",
            category="Oils",
            stock=50
        ),
        Product(
            name="Organic Mixed Seeds",
            price=149.0,
            image="seeds.jpg",
            category="Seeds",
            stock=100
        ),
        Product(
            name="Traditional Mango Pickle",
            price=399.0,
            image="pickle.jpg",
            category="Pickles",
            stock=30
        ),
    ]

    db.session.add_all(products)
    db.session.commit()

    print(f"Added {Product.query.count()} products")
    for p in Product.query.all():
        print(f"- {p.name} | ₹{p.price} | {p.category}")