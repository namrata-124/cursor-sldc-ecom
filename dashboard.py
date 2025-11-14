# dashboard.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

DB_PATH = "ecom.db"

@st.cache_data
def load_tables():
    conn = sqlite3.connect(DB_PATH)
    customers = pd.read_sql_query("SELECT * FROM customers", conn, parse_dates=["created_at"])
    products = pd.read_sql_query("SELECT * FROM products", conn)
    orders = pd.read_sql_query("SELECT * FROM orders", conn, parse_dates=["order_date"])
    order_items = pd.read_sql_query("SELECT * FROM order_items", conn)
    reviews = pd.read_sql_query("SELECT * FROM reviews", conn, parse_dates=["review_date"])
    conn.close()
    return customers, products, orders, order_items, reviews

customers, products, orders, order_items, reviews = load_tables()

st.set_page_config(layout="wide", page_title="Ecom Dashboard")

st.title("E-commerce Dashboard — cursor-sldc-ecom")

# --- Sidebar filters ---
with st.sidebar:
    st.header("Filters")
    min_date = orders['order_date'].min()
    max_date = orders['order_date'].max()
    # date_input returns list when two dates are provided
    date_range = st.date_input("Order date range", [min_date.date(), max_date.date()])
    categories = ["All"] + sorted(products['category'].dropna().unique().tolist())
    category_sel = st.selectbox("Product category", categories)
    top_n = st.slider("Top N products/customers", 5, 20, 10)

# apply filters
start_dt = pd.to_datetime(date_range[0])
end_dt = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
ord_mask = (orders['order_date'] >= start_dt) & (orders['order_date'] <= end_dt)
orders_f = orders.loc[ord_mask]

# join order_items with filtered orders and products
oi = order_items.merge(orders_f[['order_id','customer_id','order_date']], on='order_id', how='inner')
oi = oi.merge(products[['product_id','name','category']], on='product_id', how='left')

if category_sel != "All":
    oi = oi[oi['category'] == category_sel]

# create line_total for safe aggregation
oi['line_total'] = oi['quantity'] * oi['unit_price']

# KPI row
total_sales = oi['line_total'].sum()
total_orders = orders_f['order_id'].nunique()
total_customers = orders_f['customer_id'].nunique()
col1, col2, col3 = st.columns(3)
col1.metric("Total sales", f"₹{total_sales:,.2f}")
col2.metric("Orders", f"{total_orders}")
col3.metric("Active customers", f"{total_customers}")

# Sales over time (monthly)
oi['order_month'] = pd.to_datetime(oi['order_date']).dt.to_period('M').dt.to_timestamp()
sales_month = oi.groupby('order_month', as_index=False)['line_total'].sum().rename(columns={'line_total':'sales'})
fig_month = px.line(sales_month, x='order_month', y='sales', markers=True, title="Sales over time (monthly)")
st.plotly_chart(fig_month, use_container_width=True)

# Top products
prod_agg = oi.groupby(['product_id','name'], as_index=False).agg(
    total_quantity=('quantity','sum'),
    total_spent=('line_total','sum')
)
prod_top = prod_agg.sort_values('total_quantity', ascending=False).head(top_n)

st.subheader(f"Top {top_n} products by quantity")
c1, c2 = st.columns([2,1])
with c1:
    st.dataframe(prod_top[['product_id','name','total_quantity','total_spent']].rename(columns={
        'name':'product_name','total_quantity':'quantity','total_spent':'spend'
    }))
with c2:
    fig_p = px.bar(prod_top.sort_values('total_quantity'), x='total_quantity', y='name', orientation='h', title="Top products")
    st.plotly_chart(fig_p, use_container_width=True)

# Top customers
cust_agg = oi.groupby('customer_id', as_index=False).agg(total_spent=('line_total','sum'))
cust_agg = cust_agg.merge(customers[['customer_id','name']], on='customer_id', how='left')
cust_top = cust_agg.sort_values('total_spent', ascending=False).head(top_n)
st.subheader(f"Top {top_n} customers by spend")
st.dataframe(cust_top[['customer_id','name','total_spent']].rename(columns={'name':'customer_name','total_spent':'spend'}))

# Ratings distribution and recent reviews
st.subheader("Ratings distribution")
if not reviews.empty:
    rev = reviews.merge(products[['product_id','name','category']], on='product_id', how='left')
    if category_sel != "All":
        rev = rev[rev['category'] == category_sel]
    fig_r = px.histogram(rev, x='rating', nbins=5, title="Rating counts")
    st.plotly_chart(fig_r, use_container_width=True)

    st.subheader("Recent reviews")
    recent_reviews = rev.sort_values('review_date', ascending=False).head(10)[['review_date','product_id','name','customer_id','rating','review_text']]
    recent_reviews = recent_reviews.rename(columns={'name':'product_name'})
    st.dataframe(recent_reviews)
else:
    st.write("No reviews available.")

st.markdown("---")
st.caption("Data: synthetic e-commerce dataset (generated).")

