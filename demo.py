import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="BrickView", layout="wide", page_icon="🏠")

# -----------------------------
# SETUP DATABASE
# -----------------------------
@st.cache_data
def setup_database():
    conn = sqlite3.connect(r"c:\Users\HP\Downloads\realestate.db")
    listings_df = pd.read_json(r"C:\Users\HP\Downloads\listings_final_expanded.json")
    property_df = pd.read_json(r"C:\Users\HP\Downloads\property_attributes_final_expanded.json")
    agents_df   = pd.read_json(r"C:\Users\HP\Downloads\agents_cleaned.json")
    buyers_df   = pd.read_json(r"C:\Users\HP\Downloads\buyers_cleaned.json")
    sales_df    = pd.read_csv(r"C:\Users\HP\Downloads\sales_cleaned.csv")
    
    listings_df.to_sql("listings",conn, if_exists="replace", index=False)
    property_df.to_sql("property_attributes", conn, if_exists="replace", index=False)
    agents_df.to_sql("agents",conn, if_exists="replace", index=False)
    buyers_df.to_sql("buyers", conn, if_exists="replace", index=False)
    sales_df.to_sql("sales", conn, if_exists="replace", index=False)
    conn.close()

setup_database()

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    conn = sqlite3.connect(r"c:\Users\HP\Downloads\realestate.db")
    df = pd.read_sql("SELECT * FROM listings", conn)
    conn.close()
    return df

df = load_data()

# SQL QUERY  —  30 QUESTIONS
SQL_QUERIES = {

    "Property & Pricing Analysis": {

        "1.average listing price by city?": """
            SELECT city, AVG(price) AS avg_price
            FROM listings
            GROUP BY city;
        """,

        "2. What is the average price per square foot by property type?": """
        
            SELECT property_type, AVG(price / sqft) AS avg_price_per_sqft
            FROM listings
            GROUP BY property_type;
        """,

        "3. How does furnishing status impact property prices?": """
            SELECT furnishing_status, AVG(price) AS avg_price
        FROM listings
        JOIN property_attributes
        ON listings.listing_id = property_attributes.listing_id
        GROUP BY furnishing_status;
        """,

        "4. Do properties closer to metro stations command higher prices?": """
            SELECT metro_distance_km, AVG(price) AS avg_price
        FROM listings
        JOIN property_attributes
        ON listings.listing_id = property_attributes.listing_id
        GROUP BY metro_distance_km;
        """,

        "5. Are rented properties priced differently from non-rented ones?": """
            SELECT is_rented, AVG(price) AS avg_price
        FROM listings
        JOIN property_attributes
        ON listings.listing_id = property_attributes.listing_id
        GROUP BY is_rented;
        """,

        "6. How do bedrooms and bathrooms affect pricing?": """
            SELECT bedrooms, bathrooms, price
        FROM listings, property_attributes
        WHERE listings.listing_id = property_attributes.listing_id;
        """,

        "7. Do properties with parking and power backup sell at higher prices?": """
            SELECT parking_available, power_backup, price
        FROM listings, property_attributes
        WHERE listings.listing_id = property_attributes.listing_id;
        """,

        "8. How does year built influence listing price?": """
            SELECT year_built, price
        FROM listings, property_attributes
        WHERE listings.listing_id = property_attributes.listing_id;
        """,

        "9. Which cities have the highest average property prices?":"""

        SELECT city, AVG(price) AS avg_price
        FROM listings
        GROUP BY city
        ORDER BY avg_price DESC;
        """,

        "10. How are properties distributed across price buckets?": """
        SELECT 
            CASE 
                WHEN price < 200000 THEN 'Under 200K'
                WHEN price < 500000 THEN '200K - 500K'
                WHEN price < 1000000 THEN '500K - 1M'
                ELSE 'Above 1M'
            END AS price_group,
            COUNT(*) AS total
        FROM listings
        GROUP BY price_group;
        """
    },

    "Sales & Market Performance": {

        "1. What is the average days on market by city?": """
         SELECT 
            l.city, 
            AVG(s.days_on_market) AS avg_days_on_market
        FROM listings l, sales s
        WHERE l.listing_id = s.listing_id
        GROUP BY l.city;
        """,

        "2. Which property types sell the fastest?": """

        SELECT property_type, days_on_market
        FROM listings, sales
        WHERE listings.listing_id = sales.listing_id;
        """,

        "3. What percentage of properties are sold above listing price?": """

        SELECT l.price, s.sale_price
        FROM listings l, sales s
        WHERE l.listing_id = s.listing_id;
        """,

        "4. What is the sale-to-list price ratio by city?": """
    
        SELECT 
            l.city,
            AVG(s.sale_price * 1.0 / l.price) AS sale_to_list_ratio
        FROM listings l
        JOIN sales s 
        ON l.listing_id = s.listing_id
        GROUP BY l.city;
        """,

        "5. Which listings took more than 90 days to sell?": """
        SELECT listing_id, days_on_market
        FROM sales
        WHERE days_on_market > 90;
        """,

        "6. How does metro distance affect time on market?": """

        SELECT 
            metro_distance_km,
            AVG(days_on_market) AS avg_days
        FROM property_attributes p
        JOIN sales s 
        ON p.listing_id = s.listing_id
        GROUP BY metro_distance_km
        ORDER BY metro_distance_km;
        """,

        "7. What is the monthly sales trend?": """
        SELECT 
            strftime('%Y-%m', date_sold) AS month,
            COUNT(*) AS total_sales
        FROM sales
        GROUP BY month
        ORDER BY month;
        """,

        "8. Which properties are currently unsold?": """
        SELECT listing_id, city, price
        FROM listings
        WHERE listing_id NOT IN (SELECT listing_id FROM sales);
        """
    },

    "Agent Performance": {

        "1. Which agents have closed the most sales?": """
        SELECT l.agent_id, COUNT(*) AS total_sales
        FROM listings l
        JOIN sales s 
        ON l.listing_id = s.listing_id
        GROUP BY l.agent_id;
        """,

        "2. Who are the top agents by total sales revenue?": """
            SELECT l.agent_id, SUM(s.sale_price) AS total_revenue
            FROM listings l
            JOIN sales s 
            ON l.listing_id = s.listing_id
            GROUP BY l.agent_id;
        """,

        "3. Which agents close deals fastest?": """
            SELECT l.agent_id, AVG(s.days_on_market) AS avg_days
            FROM listings l
            JOIN sales s 
            ON l.listing_id = s.listing_id
            GROUP BY l.agent_id;
        """,

        "4. Does experience correlate with deals closed?": """
        SELECT a.experience_years, COUNT(*) AS total_deals
        FROM agents a
        JOIN listings l ON a.agent_id = l.agent_id
        JOIN sales s ON l.listing_id = s.listing_id
        GROUP BY a.experience_years
        ORDER BY a.experience_years;
        """,

        "5. Do agents with higher ratings close deals faster?": """
        SELECT a.rating, AVG(s.days_on_market) AS avg_days
        FROM agents a
        JOIN listings l ON a.agent_id = l.agent_id
        JOIN sales s ON l.listing_id = s.listing_id
        GROUP BY a.rating
        ORDER BY a.rating DESC;
        """,

        "6. What is the average commission earned by each agent?": """

        SELECT agent_id, AVG(commission_rate) AS avg_commission
        FROM agents
        GROUP BY agent_id;
        """,

        "7. Which agents currently have the most active listings?": """
        SELECT agent_id, COUNT(*) AS total_listings
        FROM listings
        GROUP BY agent_id;
        """
    },

    "Buyer & Financing Behavior": {

        "1. What percentage of buyers are investors vs end users?": """
        SELECT 
        buyer_type,
        COUNT(*) AS total_buyers,
        ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM buyers), 2) AS percentage
        FROM buyers
        GROUP BY buyer_type;
        """,

        "2. Which cities have the highest loan uptake rate?": """
        SELECT 
        COUNT(*) AS total_buyers,
        SUM(loan_taken) AS loan_buyers,
        (SUM(loan_taken) * 100.0 / COUNT(*)) AS percentage
        FROM buyers;
        """,

        "3. What is the average loan amount by buyer type?": """
        SELECT buyer_type, AVG(loan_amount) AS avg_loan
        FROM buyers
        GROUP BY buyer_type;
        """,

        "4. Which payment mode is most commonly used?": """
        SELECT payment_mode, COUNT(*) AS total
        FROM buyers
        GROUP BY payment_mode;
        """,

        "5. Do loan-backed purchases take longer to close?": """
        SELECT loan_taken, COUNT(*) AS total_buyers
        FROM buyers
        GROUP BY loan_taken;
        """
    }
}

# SIDEBAR(INTRODUCTION)
# -----------------------------
with st.sidebar:
    st.title("🏠 BrickView")
    st.caption("Real Estate Intelligence")
    st.divider()

    menu = st.radio(
        "Navigation",
        [
            "🏡 Introduction",
            "🔍 Filters & Explorer",
            "📊 Visualizations",
            "🗂️ CRUD Operations",
            "💾 SQL Queries"
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("© 2024 BrickView RE Platform")

page = menu.split(" ", 1)[1]

# -----------------------------
# INTRODUCTION
# -----------------------------
if page == "Introduction":

    st.title("🏠 BrickView Real Estate")
    st.subheader("Real Estate Intelligence Platform")

    st.info(
        "**BrickView Real Estate** — A smart platform for property listings, "
        "analytics, and real estate insights."
    )

    st.write(
        "A platform for exploring property listings, analyzing trends, "
        "tracking agents, and understanding buyers."
    )

    st.divider()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Listings", len(df))
    c2.metric("Total Sales", "8,752")
    c3.metric("Agents","324")
    c4.metric("Buyers", "6,521")
    c5.metric("Avg Price", "$542K")



# FILTERS & EXPLORER


elif page == "Filters & Explorer":

    st.title("🔍 Property Explorer")

    # Convert date column
    df["Date_Listed"] = pd.to_datetime(df["Date_Listed"])

    # -------- FILTERS --------
    city = st.selectbox("Select City", ["All"] + sorted(df["City"].dropna().unique()))

    price_range = st.slider(
        "Select Price Range",
        int(df["Price"].min()),
        int(df["Price"].max()),
        (int(df["Price"].min()), int(df["Price"].max()))
    )

    property_type = st.selectbox(
        "Select Property Type",
        ["All"] + sorted(df["Property_Type"].dropna().unique())
    )

    agent = st.selectbox(
        "Select Agent",
        ["All"] + sorted(df["Agent_ID"].astype(str).unique().tolist())
    )

    date_from = st.date_input("From Date", df["Date_Listed"].min().date())
    date_to   = st.date_input("To Date", df["Date_Listed"].max().date())

    # -------- FILTER LOGIC --------
    filtered_df = df.copy()

    if city != "All":
        filtered_df = filtered_df[filtered_df["City"] == city]

    if property_type != "All":
        filtered_df = filtered_df[filtered_df["Property_Type"] == property_type]

    if agent != "All":
        filtered_df = filtered_df[filtered_df["Agent_ID"].astype(str) == agent]

    filtered_df = filtered_df[
        (filtered_df["Price"] >= price_range[0]) &
        (filtered_df["Price"] <= price_range[1])
    ]

    filtered_df = filtered_df[
        (filtered_df["Date_Listed"] >= pd.to_datetime(date_from)) &
        (filtered_df["Date_Listed"] <= pd.to_datetime(date_to))
    ]

    # -------- OUTPUT --------
    st.write(f"**{len(filtered_df)} properties found**")
    st.dataframe(filtered_df, use_container_width=True)

# VISUALIZATIONS


elif page == "Visualizations":

    st.title("Real Estate Visualizations:-")

    # MAP
    st.subheader("Property Map")

    fig_map = px.scatter_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        color="Property_Type",
        zoom=4,
        height=500
    )
    fig_map.update_layout(mapbox_style="open-street-map")  # use free map tiles
    st.plotly_chart(fig_map, use_container_width=True)

    st.divider()

    #BAR CHART 
    st.subheader("📊 Avg Price by City")

    # Group data by city, calculate mean price, sort highest first
    avg_price = df.groupby("City")["Price"].mean().sort_values(ascending=False)
    st.bar_chart(avg_price)

    st.divider()

    #  PIE CHART 
    st.subheader("Property Types")

    # Count how many properties exist for each type
    counts = df["Property_Type"].value_counts()

    # Draw pie chart using matplotlib
    fig_pie, ax = plt.subplots(figsize=(2, 2))
    ax.pie(counts, labels=counts.index, autopct="%1.1f%%")  # show % on slices
    st.pyplot(fig_pie)

    st.divider()

    #  LINE CHART 
    st.subheader("Monthly Listing Trend")

    # Convert date column to datetime so we can extract month
    df["Date_Listed"] = pd.to_datetime(df["Date_Listed"])
    df["Month"] = df["Date_Listed"].dt.to_period("M").astype(str)  # e.g. "2024-01"

    # Count number of listings per month, sorted by date
    trend = df.groupby("Month").size().sort_index()
    st.line_chart(trend)

    st.divider()

    # DATA TABLE 
    st.subheader("Raw Data")

    # Show the full dataset in an interactive table
    st.dataframe(df, use_container_width=True)

# -----------------------------
# CRUD OPERATIONS
# -----------------------------
elif page == "CRUD Operations":

    st.title("CRUD Operations:-")
    st.caption("Create, Read, Update, Delete records in the database")

    def get_connection():
        return sqlite3.connect(r"c:\Users\HP\Downloads\realestate.db")

    table = st.selectbox(
        "Select Table",
        ["listings", "agents", "buyers", "sales", "property_attributes"]
    )

    operation = st.radio(
        "Operation", ["View", "Add", "Update", "Delete"], horizontal=True
    )

    conn = get_connection()
    df_table = pd.read_sql(f"SELECT * FROM {table}", conn)
    columns  = df_table.columns.tolist()
    conn.close()

    st.divider()

    if operation == "View":
        st.dataframe(df_table, use_container_width=True)

    elif operation == "Add":
        st.subheader("+Add New Record")
        data = {}
        form_cols = st.columns(3)
        non_id_cols = [c for c in columns if "id" not in c.lower()]
        for i, col in enumerate(non_id_cols):
            with form_cols[i % 3]:
                data[col] = st.text_input(col)

        if st.button("Add Record", type="primary"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                col_str      = ", ".join(data.keys())
                vals         = list(data.values())
                placeholders = ", ".join(["?"] * len(vals))
                cursor.execute(f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})", vals)
                conn.commit()
                conn.close()
                st.success("Record added successfully!")
            except Exception as e:
                st.error(f"Error: {e}")

    elif operation == "Update":
        st.subheader("Update Record")
        id_col = columns[0]
        u1, u2, u3 = st.columns(3)
        with u1:
            rid = st.text_input(f"Record ID ({id_col})")
        with u2:
            col_to_update = st.selectbox("Column to Update", columns)
        with u3:
            new_val = st.text_input("New Value")

        if st.button("Update Record", type="primary"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE {table} SET {col_to_update}=? WHERE {id_col}=?",
                    (new_val, rid)
                )
                conn.commit()
                conn.close()
                st.success("Record updated successfully!")
            except Exception as e:
                st.error(f"Error: {e}")

    elif operation == "Delete":
        st.subheader("Delete Record")
        id_col = columns[0]
        rid = st.text_input(f"Record ID ({id_col}) to delete")

        if st.button("Delete Record", type="primary"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {table} WHERE {id_col}=?", (rid,))
                conn.commit()
                conn.close()
                st.success("Record deleted successfully!")
            except Exception as e:
                st.error(f"Error: {e}")

# -----------------------------
# SQL QUERIES EXPLORER
# -----------------------------
elif page == "SQL Queries":

    st.title("SQL Queries:-")
    st.caption("Select a category and a question — the SQL query and its result table will appear instantly.")

    st.divider()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.write("**Category**")
        category = st.selectbox(
            "Category",
            list(SQL_QUERIES.keys()),
            label_visibility="collapsed"
        )

    with col2:
        st.write("**Question**")
        question = st.selectbox(
            "Question",
            list(SQL_QUERIES[category].keys()),
            label_visibility="collapsed"
        )

    st.divider()

    query = SQL_QUERIES[category][question]

    try:
        conn = sqlite3.connect(r"c:\Users\HP\Downloads\realestate.db")
        result_df = pd.read_sql(query, conn)
        conn.close()
        st.write(f"**{len(result_df):,} rows returned**")
        st.dataframe(result_df, use_container_width=True)
    except Exception as e:
        st.error(f"Query Error: {e}")

    with st.expander("View SQL Query"):
        st.code(query.strip(), language="sql")
