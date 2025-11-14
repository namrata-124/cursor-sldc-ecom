# ingest_to_sqlite.py
import sqlite3
import pandas as pd
import os

db_path = "ecom.db"
data_dir = "data"

if not os.path.exists(data_dir):
    raise SystemExit("data/ folder not found. Run generate_data.py first.")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.executescript("""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT,
    category TEXT,
    price REAL,
    sku TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date TEXT,
    total_amount REAL,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    unit_price REAL,
    FOREIGN KEY(order_id) REFERENCES orders(order_id),
    FOREIGN KEY(product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id INTEGER PRIMARY KEY,
    product_id INTEGER,
    customer_id INTEGER,
    rating INTEGER,
    review_text TEXT,
    review_date TEXT,
    FOREIGN KEY(product_id) REFERENCES products(product_id),
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orderitems_order ON order_items(order_id);
""")
conn.commit()

def load_csv_to_table(file_name, table_name):
    path = os.path.join(data_dir, file_name)
    df = pd.read_csv(path)
    df.to_sql(table_name, conn, if_exists='append', index=False)
    print(f"Inserted {len(df)} rows into {table_name}")

load_csv_to_table("customers.csv", "customers")
load_csv_to_table("products.csv", "products")
load_csv_to_table("orders.csv", "orders")
load_csv_to_table("order_items.csv", "order_items")
load_csv_to_table("reviews.csv", "reviews")

conn.commit()
conn.close()
print("Ingestion complete. DB:", db_path)
