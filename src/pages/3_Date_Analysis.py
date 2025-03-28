import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "flights_database.db")


def load_data(query):
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn)
    return df


st.markdown(
    """
<div style="display: flex; align-items: center; margin-bottom: 1rem;">
    <div style="flex: 5;">
        <h1>Date-based Analysis </h1>
        <p>Welcome to the <strong>Date Analysis</strong> section. Explore flights analysis of a specific date for New York City's airports. </p>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


def most_delayed_airlines(year, month, day):
    query = f"""
    SELECT f.carrier, a.name AS airline_name, AVG(f.arr_delay) as avg_arr_delay
    FROM flights f
    JOIN airlines a ON f.carrier = a.carrier
    WHERE f.year = {year}
      AND f.month = {month}
      AND f.day = {day}
      AND f.origin IN ('JFK','LGA','EWR')
    GROUP BY f.carrier
    ORDER BY avg_arr_delay DESC
    LIMIT 10;
    """
    df = load_data(query)
    if not df.empty:
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("avg_arr_delay:Q", title="Avg. Arrival Delay (min)"),
                y=alt.Y("airline_name:N", sort="-x", title="Airline"),
                tooltip=["airline_name", "avg_arr_delay"],
            )
            .properties(width=350, height=400, title="Most Delayed Airlines")
        )
        return chart
    return None


def top_destinations(year, month, day):
    query = f"""
    SELECT f.dest, a.name AS airport_name, COUNT(*) as flight_count
    FROM flights f
    JOIN airports a ON f.dest = a.faa
    WHERE f.year = {year}
      AND f.month = {month}
      AND f.day = {day}
      AND f.origin IN ('JFK','LGA','EWR')
    GROUP BY f.dest
    ORDER BY flight_count DESC
    LIMIT 10;
    """
    df = load_data(query)
    if not df.empty:
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("flight_count:Q", title="Number of Flights"),
                y=alt.Y("dest:N", sort="-x", title="Destination"),
                tooltip=["dest", "airport_name", "flight_count"],
            )
            .properties(width=350, height=400, title="Top 10 Destinations")
        )
        return chart
    return None


st.markdown("Pick a date to see relevant flight statistics from NYC airports.")

selected_date = st.date_input(
    "Select Date",
    value=datetime(2023, 1, 1),
    min_value=datetime(2023, 1, 1),
    max_value=datetime(2023, 12, 31),
)

if selected_date:
    year = selected_date.year
    month = selected_date.month
    day = selected_date.day

    st.write(f"**Selected date**: {selected_date.strftime('%Y-%m-%d')}")

    date_query = f"""
    SELECT 
        COUNT(*) as flight_count,
        AVG(dep_delay) as avg_dep_delay,
        AVG(arr_delay) as avg_arr_delay
    FROM flights
    WHERE year = {year}
      AND month = {month}
      AND day = {day}
      AND origin IN ('JFK','LGA','EWR');
    """
    df_date_stats = load_data(date_query)

    flight_count = (
        int(df_date_stats["flight_count"][0]) if not df_date_stats.empty else 0
    )
    avg_dep_delay = (
        round(df_date_stats["avg_dep_delay"][0],
              2) if not df_date_stats.empty else None
    )
    avg_arr_delay = (
        round(df_date_stats["avg_arr_delay"][0],
              2) if not df_date_stats.empty else None
    )

    if flight_count > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Number of Flights</div>
                    <div class="metric-value">{flight_count}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Avg. Departure Delay </div>
                    <div class="metric-value">{avg_dep_delay} min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Avg. Arrival Delay </div>
                    <div class="metric-value">{avg_arr_delay} min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        airline_query = f"""
        SELECT f.carrier, a.name AS airline_name, COUNT(*) as flight_count
        FROM flights f
        JOIN airlines a ON f.carrier = a.carrier
        WHERE f.year = {year}
          AND f.month = {month}
          AND f.day = {day}
          AND f.origin IN ('JFK','LGA','EWR')
        GROUP BY f.carrier
        ORDER BY flight_count DESC;
        """
        df_airline_date = load_data(airline_query)

        if not df_airline_date.empty:
            date_bar = (
                alt.Chart(df_airline_date)
                .mark_bar()
                .encode(
                    x=alt.X("flight_count:Q", title="Number of Flights"),
                    y=alt.Y("airline_name:N", sort="-x", title="Airline"),
                    tooltip=["airline_name", "flight_count"],
                )
                .properties(
                    width=700, height=400, title="Flights by Airline on Selected Date"
                )
            )
            st.altair_chart(date_bar, use_container_width=True)
        else:
            st.info("No flights found by airline for this date.")

        col4, col5 = st.columns(2)
        delayed_chart = most_delayed_airlines(year, month, day)
        top_dest_chart = top_destinations(year, month, day)

        if delayed_chart:
            col4.altair_chart(delayed_chart, use_container_width=True)
        if top_dest_chart:
            col5.altair_chart(top_dest_chart, use_container_width=True)

    else:
        st.warning("No flights found on this date.")
