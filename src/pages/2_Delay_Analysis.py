import math
import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from textwrap import dedent
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..",
                       "..", "flights_database.db")

st.set_page_config(page_title="Flight Delay Analysis",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stApp {
        background-color: #f8f9fa;
    }
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
    }
    .polar-chart {
        width: 100%;
        height: 400px;
    }
</style>
""", unsafe_allow_html=True)


def get_connection():
    return sqlite3.connect(DB_PATH)


def run_query(query):
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


# Dashboard title
st.title("✈️ Flight Delay Analysis Dashboard")
st.markdown("<div class='card'><p>This dashboard analyzes flight delays with a focus on NYC airports. Select your analysis mode below.</p></div>", unsafe_allow_html=True)

# Analysis mode selection
analysis_mode = st.radio(
    "Select Analysis Mode:",
    ["Airport Analysis", "Specific Route Analysis"],
    horizontal=True
)

st.sidebar.header("Filters")

nyc_airports_query = """
SELECT DISTINCT faa, name
FROM airports
WHERE faa IN ('JFK', 'LGA', 'EWR')
"""
nyc_airports = run_query(nyc_airports_query)

date_range_query = """
SELECT MIN(year || '-' || PRINTF('%02d', month) || '-' || PRINTF('%02d', day)) as min_date,
       MAX(year || '-' || PRINTF('%02d', month) || '-' || PRINTF('%02d', day)) as max_date
FROM flights
"""
date_range = run_query(date_range_query)
min_date = datetime.strptime(date_range['min_date'][0], '%Y-%m-%d').date()
max_date = datetime.strptime(date_range['max_date'][0], '%Y-%m-%d').date()

start_date = st.sidebar.date_input(
    "Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", min(
    max_date, start_date + timedelta(days=30)), min_value=start_date, max_value=max_date)

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')


# AIRPORT ANALYSIS MODE
if analysis_mode == "Airport Analysis":
    st.sidebar.subheader("Airport Selection")
    origin_airport = st.sidebar.selectbox(
        "Select Airport", nyc_airports['faa'],
        format_func=lambda x: f"{x} - {nyc_airports[nyc_airports['faa'] == x]['name'].values[0]}")

    # Query for airport data
    airport_query = f"""
    SELECT
        f.year, f.month, f.day,
        f.dep_time, f.dep_delay,
        f.arr_delay, f.carrier,
        f.origin, f.dest,
        f.distance,
        al.name as airline_name
    FROM
        flights f
    JOIN
        airlines al ON f.carrier = al.carrier
    WHERE
        f.origin = '{origin_airport}'
        AND date(f.year || '-' || PRINTF('%02d', f.month) || '-' || PRINTF('%02d', f.day))
            BETWEEN date('{start_date_str}') AND date('{end_date_str}')
    """

    airport_data = run_query(airport_query)

    if airport_data.empty:
        st.warning(
            f"No flights found for {origin_airport} in the selected date range.")
    else:
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown("<div>", unsafe_allow_html=True)
            st.subheader("Airport Metrics")

            total_flights = len(airport_data)
            avg_dep_delay = airport_data['dep_delay'].mean(
            ) if not airport_data['dep_delay'].empty else 0
            avg_arr_delay = airport_data['arr_delay'].mean(
            ) if not airport_data['arr_delay'].empty else 0
            delayed_flights = airport_data[airport_data['dep_delay']
                                           > 15].shape[0]
            delay_rate = (delayed_flights / total_flights) * \
                100 if total_flights > 0 else 0

            st.metric("Total Flights", f"{total_flights}")
            st.metric("Average Departure Delay", f"{avg_dep_delay:.1f} min")
            st.metric("Average Arrival Delay", f"{avg_arr_delay:.1f} min")
            st.metric("Delayed Flights (>15min)", f"{delay_rate:.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div>", unsafe_allow_html=True)
            st.subheader("Daily Delay Distribution")

            # Group by date and calculate average delays
            daily_delays = airport_data.copy()
            daily_delays['date'] = pd.to_datetime(
                daily_delays[['year', 'month', 'day']])
            daily_delays = daily_delays.groupby('date').agg({
                'dep_delay': 'mean',
                'arr_delay': 'mean'
            }).reset_index()

            fig_daily = go.Figure()
            fig_daily.add_trace(go.Bar(
                x=daily_delays['date'],
                y=daily_delays['dep_delay'],
                name='Departure Delay',
                marker_color='#4285F4'
            ))
            fig_daily.add_trace(go.Bar(
                x=daily_delays['date'],
                y=daily_delays['arr_delay'],
                name='Arrival Delay',
                marker_color='#EA4335'
            ))
            fig_daily.update_layout(
                barmode='group',
                xaxis_title='Date',
                yaxis_title='Average Delay (minutes)',
                legend=dict(orientation="h", yanchor="bottom",
                            y=1.02, xanchor="right", x=1),
                height=400,
                margin=dict(l=40, r=40, t=40, b=40)
            )
            st.plotly_chart(fig_daily, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)


################

st.markdown("""
<div style="text-align:center; margin-top: 40px; padding: 20px; color: #6c757d;">
    <p>✈️ Flight Delay Analysis Dashboard | Data Engineering Project</p>
</div>
""", unsafe_allow_html=True)
