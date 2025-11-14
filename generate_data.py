# generate_data.py
from faker import Faker
import pandas as pd
import random
import os

fake = Faker()
SEED = 42
random.seed(SEED)
Faker.seed(SEED)

os.makedirs("data", exist_ok=True)

# customers
customers = []
for i in range(1, 201):
    customers.append({
        "customer_id": i,
        "name": fake.name(),
        "email": fake.email(),
        "created_at": fake.date_time_between(start_date='-3y', end_date='now').isoformat()
    })
pd.DataFrame(customers).to_csv("data/customers.csv", index=False)

# products
categories = ["electronics", "clothing", "home", "books", "toys"]
products = []
for i in range(1, 101):
    products.append({
        "product_id": i,
        "name": fake.word().title() + " " + fake.word().title(),
        "category": random.choice(categories),
        "price": round(random.uniform(5, 500), 2),
        "sku": f"SKU{i:05d}"
    })
pd.DataFrame(products).to_csv("data/products.csv", index=False)

# orders and order_items
orders = []
order_items = []
order_item_id = 1
for order_id in range(1, 1001):
    customer_id = random.randint(1, 200)
    order_date = fake.date_time_between(start_date='-2y', end_date='now')
    n_items = random.randint(1, 5)
    total = 0.0
    for _ in range(n_items):
        prod = random.choice(products)
        qty = random.randint(1, 3)
        unit = prod["price"]
        total += qty * unit
        order_items.append({
            "order_item_id": order_item_id,
            "order_id": order_id,
            "product_id": prod["product_id"],
            "quantity": qty,
            "unit_price": unit
        })
        order_item_id += 1
    orders.append({
        "order_id": order_id,
        "customer_id": customer_id,
        "order_date": order_date.isoformat(),
        "total_amount": round(total, 2)
    })

pd.DataFrame(orders).to_csv("data/orders.csv", index=False)
pd.DataFrame(order_items).to_csv("data/order_items.csv", index=False)

# reviews
reviews = []
review_id = 1
for _ in range(400):
    prod_id = random.randint(1, 100)
    cust_id = random.randint(1, 200)
    reviews.append({
        "review_id": review_id,
        "product_id": prod_id,
        "customer_id": cust_id,
        "rating": random.randint(1, 5),
        "review_text": fake.sentence(nb_words=12),
        "review_date": fake.date_time_between(start_date='-2y', end_date='now').isoformat()
    })
    review_id += 1
pd.DataFrame(reviews).to_csv("data/reviews.csv", index=False)

print("Generated CSVs in data/ folder")
