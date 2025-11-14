# dashboard.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

DB_PATH = "ecom.db"

# Color palette (pleasant, modern)
PALETTE = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]

@st.cache_data
def load_tables():
    conn = sqlite3.connect(DB_PATH)
    customers = pd.read_sql_query("SELECT * FROM customers", conn)
    products = pd.read_sql_query("SELECT * FROM products", conn)
    orders = pd.read_sql_query("SELECT * FROM orders", conn, parse_dates=["order_date"])
    order_items = pd.read_sql_query("SELECT * FROM order_items", conn)
    reviews = pd.read_sql_query("SELECT * FROM reviews", conn, parse_dates=["review_date"])
    conn.close()
    return customers, products, orders, order_items, reviews

customers, products, orders, order_items, reviews = load_tables()

st.set_page_config(layout="wide", page_title="E-commerce Dashboard", initial_sidebar_state="expanded")

# Top header
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:16px">
      <div style="font-size:26px;font-weight:700">E-commerce Dashboard</div>
      <div style="color:gray">— cursor-sldc-ecom (synthetic dataset)</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")  # spacing

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    try:
        min_date = orders['order_date'].min().date()
        max_date = orders['order_date'].max().date()
    except Exception:
        # fallback if parse failed
        orders['order_date'] = pd.to_datetime(orders['order_date'])
        min_date = orders['order_date'].min().date()
        max_date = orders['order_date'].max().date()

    date_range = st.date_input("Order date range", (min_date, max_date))
    categories = ["All"] + sorted(products['category'].dropna().unique().tolist())
    category_sel = st.selectbox("Product category", categories)
    top_n = st.slider("Top N products/customers", 5, 20, 10)
    show_reviews = st.checkbox("Show recent reviews panel", value=True)

# Apply filters
start_dt = pd.to_datetime(date_range[0])
end_dt = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)

orders_f = orders[(orders['order_date'] >= start_dt) & (orders['order_date'] < end_dt)]

oi = order_items.merge(
    orders_f[['order_id', 'customer_id', 'order_date']],
    on='order_id',
    how='inner'
)

oi = oi.merge(products[['product_id', 'name', 'category']], on='product_id', how='left')

if category_sel != "All":
    oi = oi[oi['category'] == category_sel]

# Add line_total for aggregation
oi['line_total'] = oi['quantity'] * oi['unit_price']

# KPI metrics
total_sales = oi['line_total'].sum()
total_orders = orders_f['order_id'].nunique()
total_customers = orders_f['customer_id'].nunique()

k1, k2, k3 = st.columns([1.5, 1, 1])
k1.metric("Total sales", f"₹{total_sales:,.2f}")
k2.metric("Orders", f"{total_orders}")
k3.metric("Active customers", f"{total_customers}")

st.markdown("---")

# Sales trend
oi['order_month'] = oi['order_date'].dt.to_period('M').dt.to_timestamp()
sales_month = oi.groupby('order_month', as_index=False)['line_total'].sum().rename(columns={'line_total': 'sales'})

fig_month = px.line(
    sales_month,
    x='order_month',
    y='sales',
    markers=True,
    title="Sales over time (monthly)",
    color_discrete_sequence=[PALETTE[0]]
)
fig_month.update_layout(title={'x':0.01})
st.plotly_chart(fig_month, use_container_width=True)

# Top products & customers
prod_agg = oi.groupby(['product_id', 'name'], as_index=False).agg(
    total_quantity=('quantity', 'sum'),
    total_spent=('line_total', 'sum')
)
prod_top = prod_agg.sort_values('total_quantity', ascending=False).head(top_n)

cust_agg = oi.groupby('customer_id', as_index=False).agg(
    total_spent=('line_total', 'sum')
).merge(customers[['customer_id','name']], on='customer_id', how='left')
cust_top = cust_agg.sort_values('total_spent', ascending=False).head(top_n)

col_left, col_right = st.columns([2,1])
with col_left:
    st.subheader(f"Top {top_n} Products by Quantity")
    st.dataframe(prod_top[['product_id','name','total_quantity','total_spent']].rename(columns={'name':'product_name'}), height=300)

with col_right:
    st.subheader(f"Top {top_n} Customers by Spend")
    st.dataframe(cust_top[['customer_id','name','total_spent']].rename(columns={'name':'customer_name'}), height=300)

# ---------- Ratings visuals (Pie, Bar, Donut) ----------
st.markdown("### Ratings — multiple views")
rev = reviews.merge(products[['product_id', 'category', 'name']], on='product_id', how='left')
if category_sel != "All":
    rev = rev[rev['category'] == category_sel]

if rev.empty:
    st.write("No reviews available for this filter.")
else:
    # compute counts
    rating_counts = rev['rating'].value_counts().sort_index().reset_index()
    rating_counts.columns = ['rating', 'count']

    # convert rating to string for nicer labels
    rating_counts['rating_str'] = rating_counts['rating'].astype(str) + " ★"

    # layout three charts in a row
    c1, c2, c3 = st.columns(3)

    # Pie chart (left)
    with c1:
        fig_pie = px.pie(
            rating_counts,
            names='rating_str',
            values='count',
            title="Rating Share (Pie)",
            color_discrete_sequence=PALETTE
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fig_pie, use_container_width=True, height=320)

    # Bar chart (middle)
    with c2:
        fig_bar = px.bar(
            rating_counts.sort_values('rating'),
            x='rating_str',
            y='count',
            title="Rating Counts (Bar)",
            text='count',
            color='rating_str',
            color_discrete_sequence=PALETTE
        )
        fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
        fig_bar.update_layout(yaxis_title="Count", showlegend=False, margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fig_bar, use_container_width=True, height=320)

    # Donut chart (right)
    with c3:
        fig_donut = px.pie(
            rating_counts,
            names='rating_str',
            values='count',
            hole=0.45,
            title="Rating Distribution (Donut)",
            color_discrete_sequence=PALETTE
        )
        fig_donut.update_traces(textinfo='percent+label')
        fig_donut.update_layout(margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fig_donut, use_container_width=True, height=320)

# Recent reviews panel (optional)
if show_reviews and not rev.empty:
    st.markdown("---")
    st.subheader("Recent Reviews")
    recent_reviews = rev.sort_values('review_date', ascending=False).head(12)[['review_date','product_id','name','customer_id','rating','review_text']]
    recent_reviews = recent_reviews.rename(columns={'name':'product_name'})
    st.dataframe(recent_reviews)

st.markdown("---")
st.caption("Designed with a modern palette — blue/teal/green/purple/orange.")
