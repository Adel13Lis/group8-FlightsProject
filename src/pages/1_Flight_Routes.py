import streamlit as st
import sqlite3
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px

# Set the database path to match the user's folder
DB_PATH = "/Users/nikolinamicek/Desktop/data_engineering/projectFlights-group8-main-3/flights_database.db"

def load_data(query):
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn)
    return df

st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 1rem;">
    <div style="flex: 5;">
        <h1>Flight Routes Page 🛩</h1>
        <p>Welcome to the <strong>Flight Routes</strong> section. Here, you can explore different flight routes from New York City's major airports to destinations worldwide.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    h1, h2, h3 {
        color: #0e4d92;
    }
    .main {
        background-color: #f8f9fa;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 16px;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #333;
    }
    .metric-label {
        font-size: 1.1rem;
        color: #555;
        margin-bottom: 5px;
    }
    .chart-container {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .airport-subtitle {
        color: #808080;
        font-size: 0.8rem;
        margin-top: -10px;
        padding-bottom: 10px;
    }
    .stPlotlyChart {
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.header("Select Route")
#Query to get unique airport codes from NYC airports only
airport_query = """
SELECT DISTINCT faa 
FROM airports
WHERE faa IN ('JFK', 'LGA', 'EWR')
ORDER BY faa
"""
df_airports = load_data(airport_query)
airport_list = df_airports['faa'].tolist()

origin = st.sidebar.selectbox(
    "Choose Departure Airport (origin)", options=airport_list, index=0)

#Query to get all unique airport codes for destinations
dest_query = """
SELECT DISTINCT faa 
FROM airports
ORDER BY faa
"""
df_dest_airports = load_data(dest_query)
dest_airport_list = df_dest_airports['faa'].tolist()

dest = st.sidebar.selectbox(
    "Choose Arrival Airport (destination)", options=dest_airport_list, index=1)

st.write(f"### Selected Route: {origin} \u27A1 {dest}")

st.markdown("---")
