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
    .toggle-container {
        display: flex;
        justify-content: center;
        margin-bottom: 15px;
    }
    .flight-info-card {
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
            margin-bottom: 20px;
        }
        .flight-info-card h4 {
            margin-top: 0;
            color: #1E1E1E;
        }
        .flight-detail {
            font-size: 14px;
            color: #5B5B5B;
            margin: 5px 0;
        }
        .delay-badge {
            background-color: #EA4335;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: 500;
            display: inline-block;
            margin-left: 8px;
        }
        .on-time-badge {
            background-color: #34A853;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: 500;
            display: inline-block;
            margin-left: 8px;
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
st.markdown("<div class='card'><p>This page analyzes flight delays with a focus on NYC airports. Select your analysis mode below.</p></div>", unsafe_allow_html=True)

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

        # Second row
        st.markdown("<div>", unsafe_allow_html=True)

        chart_title = f"Top 5 Destinations with Highest Delay"

        st.subheader(chart_title)

        delay_type = st.radio(
            "Select Delay Type:",
            ["Departure Delays", "Arrival Delays"],
            horizontal=True,
            key="delay_type_toggle"
        )

        delay_column = 'dep_delay' if delay_type == "Departure Delays" else 'arr_delay'
        chart_color = '#1E3A8A' if delay_type == "Departure Delays" else '#E1A95F'

        top_delayed_destinations = (
            airport_data.groupby(['dest'])
            .agg({
                delay_column: ['mean', 'count'],
                'airline_name': 'first'
            })
            .reset_index()
        )

        top_delayed_destinations.columns = [
            'dest', 'avg_delay', 'flight_count', 'airline_name']

        top_delayed_destinations = top_delayed_destinations[
            top_delayed_destinations['flight_count'] >= 10]

        top_delayed_destinations = top_delayed_destinations.sort_values(
            'avg_delay', ascending=False).head(5)

        if not top_delayed_destinations.empty:
            airports_query = f"""
            SELECT faa, name 
            FROM airports 
            WHERE faa IN ({', '.join([f"'{dest}'" for dest in top_delayed_destinations['dest']])})
            """
            destination_airports = run_query(airports_query)

            airport_names = dict(
                zip(destination_airports['faa'], destination_airports['name']))

            top_delayed_destinations['airport_name'] = top_delayed_destinations['dest'].map(
                lambda code: f"{code} - {airport_names.get(code, 'Unknown Airport')}")

            fig_top_delays = go.Figure()

            fig_top_delays.add_trace(go.Bar(
                y=top_delayed_destinations['airport_name'],
                x=top_delayed_destinations['avg_delay'],
                marker_color=chart_color,
                orientation='h',
                text=[
                    f"{delay:.1f} min" for delay in top_delayed_destinations['avg_delay']],
                textposition='inside',
                insidetextanchor='end',
                textfont=dict(color='white', size=14),
                width=0.7,
                name='Average Delay'
            ))

            for i, (airport, delay, count) in enumerate(zip(
                top_delayed_destinations['airport_name'],
                top_delayed_destinations['avg_delay'],
                top_delayed_destinations['flight_count']
            )):
                fig_top_delays.add_annotation(
                    x=delay + 1,
                    y=airport,
                    text=f"{count} flights",
                    showarrow=False,
                    font=dict(size=12),
                    xanchor='left'
                )

            fig_top_delays.update_layout(
                height=400,
                margin=dict(l=20, r=120, t=60, b=40),
                xaxis_title='Average Delay (minutes)',
                yaxis_title='',
                plot_bgcolor='white',
                yaxis=dict(
                    showgrid=False,
                    autorange="reversed"
                ),
                xaxis=dict(
                    zeroline=False,
                    showgrid=True,
                    gridcolor='lightgray'
                ),
                showlegend=False
            )

            st.plotly_chart(fig_top_delays, use_container_width=True)
        else:
            st.warning(
                f"No destinations with sufficient flights found for {delay_type} analysis.")

        st.markdown("</div>", unsafe_allow_html=True)


# SPECIFIC ROUTE ANALYSIS MODE
elif analysis_mode == "Specific Route Analysis":
    st.sidebar.subheader("Route Selection")

    dest_airports_query = """
    SELECT DISTINCT a.faa, a.name, a.tzone
    FROM airports a
    JOIN flights f ON a.faa = f.dest
    WHERE f.origin IN ('JFK', 'LGA', 'EWR')
    ORDER BY a.name
    """
    dest_airports = run_query(dest_airports_query)

    origin_airport = st.sidebar.selectbox(
        "Departure Airport",
        nyc_airports['faa'],
        format_func=lambda x: f"{x} - {nyc_airports[nyc_airports['faa'] == x]['name'].values[0]}")

    dest_airport = st.sidebar.selectbox(
        "Arrival Airport",
        dest_airports['faa'],
        format_func=lambda x: f"{x} - {dest_airports[dest_airports['faa'] == x]['name'].values[0]}"
    )

    dest_tzone = dest_airports[dest_airports['faa']
                               == dest_airport]['tzone'].values[0]

    # Query for Route data
    route_query = f"""
    SELECT
        f.year, f.month, f.day,
        f.dep_time, f.sched_dep_time, f.dep_delay,
        f.arr_time, f.sched_arr_time, f.arr_delay,
        f.carrier, f.flight, f.tailnum, f.origin, f.dest,
        f.air_time, f.distance,
        al.name as airline_name,
        orig.name as origin_name, orig.lat as origin_lat, orig.lon as origin_lon,
        dest.name as dest_name, dest.lat as dest_lat, dest.lon as dest_lon,
        dest.tzone as dest_tzone
    FROM
        flights f
    JOIN
        airlines al ON f.carrier = al.carrier
    JOIN
        airports orig ON f.origin = orig.faa
    JOIN
        airports dest ON f.dest = dest.faa
    WHERE
        f.origin = '{origin_airport}'
        AND f.dest = '{dest_airport}'
        AND date(f.year || '-' || PRINTF('%02d', f.month) || '-' || PRINTF('%02d', f.day))
            BETWEEN date('{start_date_str}') AND date('{end_date_str}')
    ORDER BY
        f.year, f.month, f.day, f.dep_time
    """
    route_data = run_query(route_query)

    # Query for weather data
    weather_query = f"""
    SELECT
        w.origin, w.year, w.month, w.day, w.hour,
        w.temp, w.dewp, w.humid, w.wind_dir, w.wind_speed, w.wind_gust,
        w.precip, w.pressure, w.visib
    FROM
        weather w
    WHERE
        w.origin = '{origin_airport}'
        AND date(w.year || '-' || PRINTF('%02d', w.month) || '-' || PRINTF('%02d', w.day))
            BETWEEN date('{start_date_str}') AND date('{end_date_str}')
    ORDER BY
        w.year, w.month, w.day, w.hour
    """
    weather_data = run_query(weather_query)

    if route_data.empty:
        st.warning(
            f"No flights found for the selected route ({origin_airport} to {dest_airport}) in the date range.")
    else:
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown("<div>", unsafe_allow_html=True)
            st.subheader("Route Metrics")

            total_flights = len(route_data)
            avg_dep_delay = route_data['dep_delay'].mean(
            ) if not route_data['dep_delay'].empty else 0
            avg_arr_delay = route_data['arr_delay'].mean(
            ) if not route_data['arr_delay'].empty else 0
            delayed_flights = route_data[route_data['dep_delay'] > 15].shape[0]
            delay_rate = (delayed_flights / total_flights) * \
                100 if total_flights > 0 else 0

            st.metric("Total Flights", f"{total_flights}")
            st.metric("Average Departure Delay", f"{avg_dep_delay:.1f} min")
            st.metric("Average Arrival Delay", f"{avg_arr_delay:.1f} min")
            st.metric("Delayed Flights (>15min)", f"{delay_rate:.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div>", unsafe_allow_html=True)
            st.subheader("Flight Route Map")

            if not route_data.empty:
                origin_lat = route_data['origin_lat'].iloc[0]
                origin_lon = route_data['origin_lon'].iloc[0]
                dest_lat = route_data['dest_lat'].iloc[0]
                dest_lon = route_data['dest_lon'].iloc[0]
                dest_tzone = route_data['dest_tzone'].iloc[0]

                fig_map = go.Figure()

                if dest_tzone and (dest_tzone.startswith('Europe/') or dest_tzone.startswith('Pacific/')):
                    map_scope = 'world'
                else:
                    map_scope = 'usa'

                if map_scope == 'usa':
                    fig_map.add_trace(go.Choropleth(
                        locations=["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                                   "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                                   "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                                   "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                                   "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"],
                        locationmode="USA-states",
                        z=[0] * 50,  # Just to create the outline
                        colorscale=[[0, 'rgba(255,255,255,0)'], [
                            1, 'rgba(255,255,255,0)']],
                        showscale=False,
                        marker_line_color='rgb(150, 150, 150)',
                        marker_line_width=0.5
                    ))

                fig_map.add_trace(go.Scattergeo(
                    lon=[origin_lon, dest_lon],
                    lat=[origin_lat, dest_lat],
                    mode='lines',
                    line=dict(width=3, color='#4285F4'),
                    opacity=0.8,
                    name='Flight Path'
                ))

                fig_map.add_trace(go.Scattergeo(
                    lon=[origin_lon, dest_lon],
                    lat=[origin_lat, dest_lat],
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=['#6A0DAD', '#6A0DAD'],
                        symbol='circle'
                    ),
                    text=[origin_airport, dest_airport],
                    hoverinfo='text',
                    name='Airports'
                ))

                if map_scope == 'usa':
                    geo_layout = dict(
                        scope='usa',
                        projection_type='albers usa',
                        showland=True,
                        landcolor='rgb(255, 255, 255)',
                        countrycolor='rgb(255, 255, 255)',
                        lakecolor='rgb(255, 255, 255)',
                        showlakes=True,
                        showocean=True,
                        oceancolor='rgb(255, 255, 255)',
                        showcoastlines=True,
                        coastlinecolor='rgb(150, 150, 150)',
                        showframe=False,
                        showcountries=True,
                        countrywidth=0.5,
                        showsubunits=True,
                        subunitwidth=0.5,
                        subunitcolor='rgb(150, 150, 150)'
                    )
                else:
                    geo_layout = dict(
                        scope='world',
                        projection_type='natural earth',
                        showland=True,
                        landcolor='rgb(255, 255, 255)',
                        countrycolor='rgb(150, 150, 150)',
                        lakecolor='rgb(255, 255, 255)',
                        showlakes=True,
                        showocean=True,
                        oceancolor='rgb(255, 255, 255)',
                        showcoastlines=True,
                        coastlinecolor='rgb(150, 150, 150)',
                        showframe=False,
                        showcountries=True,
                        countrywidth=0.5,
                        showsubunits=True,
                        subunitwidth=0.5,
                        subunitcolor='rgb(150, 150, 150)',
                    )

                fig_map.update_layout(
                    geo=geo_layout,
                    height=400,
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor='rgb(255, 255, 255)',
                    plot_bgcolor='rgb(255, 255, 255)',
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01,
                        bgcolor="rgba(255, 255, 255, 0.7)"
                    )
                )

                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning("No route data available to display map")

            st.markdown("</div>", unsafe_allow_html=True)

        # Second row: Wind analysis and daily delays
        st.markdown("<div>", unsafe_allow_html=True)
        st.subheader("🌪️ Wind Direction and Flight Path Analysis")

        if not route_data.empty:
            if 'year' in route_data.columns and 'month' in route_data.columns and 'day' in route_data.columns and 'dep_time' in route_data.columns:
                route_data = route_data.sort_values(
                    by=['year', 'month', 'day', 'dep_time'])

            flight_ids = route_data.index.tolist()

            flight_labels = []
            for idx in flight_ids:
                flight_row = route_data.loc[idx]

                flight_date = f"{flight_row['year']}-{flight_row['month']:02d}-{flight_row['day']:02d}"

                dep_time = flight_row.get('dep_time', '')
                if pd.notna(dep_time) and dep_time != '':
                    dep_time_str = str(int(dep_time)).zfill(4) if isinstance(
                        dep_time, (int, float)) else str(dep_time).zfill(4)
                    dep_time_formatted = f"{dep_time_str[:2]}:{dep_time_str[2:]}"
                else:
                    dep_time_formatted = "N/A"

                arr_time = flight_row.get('arr_time', '')
                if pd.notna(arr_time) and arr_time != '':
                    arr_time_str = str(int(arr_time)).zfill(4) if isinstance(
                        arr_time, (int, float)) else str(arr_time).zfill(4)
                    arr_time_formatted = f"{arr_time_str[:2]}:{arr_time_str[2:]}"
                else:
                    arr_time_formatted = "N/A"

                dep_delay = flight_row.get('dep_delay', 0)
                arr_delay = flight_row.get('arr_delay', 0)

                delay_status = ""
                if pd.notna(dep_delay) and dep_delay > 15:
                    delay_status = " [DEPARTURE DELAYED]"
                elif pd.notna(arr_delay) and arr_delay > 15:
                    delay_status = " [ARRIVAL DELAYED]"

                label = f"{flight_date} | Flight {flight_row['carrier']}{flight_row['flight']} | "
                label += f"Dep: {dep_time_formatted} → Arr: {arr_time_formatted} | "
                label += f"Tail: {flight_row.get('tailnum', 'N/A')}{delay_status}"

                flight_labels.append(label)

            flight_options = dict(zip(flight_labels, flight_ids))

            st.markdown("### Flight Selection")

            selected_flight_label = st.selectbox(
                "Choose a flight to view its wind direction analysis:",
                options=flight_labels,
                index=0,
            )

            flight_row = route_data.loc[flight_options[selected_flight_label]]

            dep_time_str = str(int(flight_row.get('dep_time', 0))).zfill(4)
            dep_time_formatted = f"{dep_time_str[:2]}:{dep_time_str[2:]}"

            arr_time_str = str(int(flight_row.get('arr_time', 0))).zfill(4)
            arr_time_formatted = f"{arr_time_str[:2]}:{arr_time_str[2:]}"

            flight_date = f"{flight_row['year']}-{flight_row['month']:02d}-{flight_row['day']:02d}"

            is_delayed = False
            delay_badge = ""

            if pd.notna(flight_row.get('dep_delay', 0)) and flight_row.get('dep_delay', 0) > 15:
                is_delayed = True
                delay_badge = "<span class='delay-badge'>DELAYED</span>"
            else:
                delay_badge = "<span class='on-time-badge'>ON TIME</span>"

            st.markdown(f"""
            <div class="flight-info-card">
                <h4>Flight {flight_row['carrier']}{flight_row['flight']} {delay_badge}</h4>
                <div class="flight-detail"><strong>Date:</strong> {flight_date}</div>
                <div class="flight-detail"><strong>Departure:</strong> {dep_time_formatted} | <strong>Arrival:</strong> {arr_time_formatted}</div>
            </div>
            """, unsafe_allow_html=True)

            selected_flight_id = flight_options[selected_flight_label]
            selected_flight = route_data.loc[selected_flight_id]

            origin_lat = selected_flight['origin_lat'] if 'origin_lat' in selected_flight else origin_lat
            origin_lon = selected_flight['origin_lon'] if 'origin_lon' in selected_flight else origin_lon
            dest_lat = selected_flight['dest_lat'] if 'dest_lat' in selected_flight else dest_lat
            dest_lon = selected_flight['dest_lon'] if 'dest_lon' in selected_flight else dest_lon

            # Get weather data for the selected flight
            if pd.notna(selected_flight['dep_time']) and selected_flight['dep_time'] != '':
                if isinstance(selected_flight['dep_time'], (int, float)):
                    dep_hour = int(selected_flight['dep_time'] // 100)
                else:
                    try:
                        dep_hour = int(str(selected_flight['dep_time'])[:2])
                    except:
                        dep_hour = 12
            else:
                if pd.notna(selected_flight['sched_dep_time']) and selected_flight['sched_dep_time'] != '':
                    if isinstance(selected_flight['sched_dep_time'], (int, float)):
                        dep_hour = int(
                            selected_flight['sched_dep_time'] // 100)
                    else:
                        try:
                            dep_hour = int(
                                str(selected_flight['sched_dep_time'])[:2])
                        except:
                            dep_hour = 12
                else:
                    dep_hour = 12

            selected_weather_data = weather_data[
                (weather_data['year'] == selected_flight['year']) &
                (weather_data['month'] == selected_flight['month']) &
                (weather_data['day'] == selected_flight['day'])
            ]

            if not selected_weather_data.empty and 'hour' in selected_weather_data.columns:
                selected_weather_data['hour_diff'] = abs(
                    selected_weather_data['hour'] - dep_hour)
                min_hour_diff = selected_weather_data['hour_diff'].min()
                selected_weather_data = selected_weather_data[
                    selected_weather_data['hour_diff'] == min_hour_diff]

            wind_cols = st.columns(2)

            with wind_cols[0]:
                def calculate_bearing(lat1, lon1, lat2, lon2):
                    lat1, lon1, lat2, lon2 = map(
                        math.radians, [lat1, lon1, lat2, lon2])
                    dlon = lon2 - lon1
                    y = math.sin(dlon) * math.cos(lat2)
                    x = math.cos(lat1) * math.sin(lat2) - \
                        math.sin(lat1) * math.cos(lat2) * \
                        math.cos(dlon)
                    initial_bearing = math.atan2(y, x)
                    initial_bearing = math.degrees(initial_bearing)
                    compass_bearing = (initial_bearing + 360) % 360
                    return compass_bearing

                flight_bearing = calculate_bearing(
                    origin_lat, origin_lon,
                    dest_lat, dest_lon
                )

                if not selected_weather_data.empty:
                    wind_data = selected_weather_data.dropna(
                        subset=['wind_dir', 'wind_speed'])

                    if not wind_data.empty:
                        avg_wind_dir = wind_data['wind_dir'].mean()
                        avg_wind_speed = wind_data['wind_speed'].mean()

                        wind_flight_angle = (
                            avg_wind_dir - flight_bearing + 360) % 360

                        is_favorable = (wind_flight_angle < 45) or (
                            wind_flight_angle > 315)

                        fig_polar = go.Figure()

                        fig_polar.add_trace(go.Scatterpolar(
                            r=[0, 1],
                            theta=[flight_bearing, flight_bearing],
                            mode='lines',
                            line=dict(color='#4285F4', width=4),
                            name=f'Flight Direction ({flight_bearing:.1f}°)'
                        ))

                        fig_polar.add_trace(go.Scatterpolar(
                            r=[0, avg_wind_speed /
                                max(wind_data['wind_speed'].max(), 1)],
                            theta=[avg_wind_dir, avg_wind_dir],
                            mode='lines',
                            line=dict(color='#FBBC05', width=4),
                            name=f'Wind Direction ({avg_wind_dir:.1f}°)'
                        ))

                        fig_polar.update_layout(
                            polar=dict(
                                radialaxis=dict(visible=True, range=[0, 1]),
                                angularaxis=dict(
                                    tickmode='array',
                                    tickvals=[0, 45, 90, 135,
                                              180, 225, 270, 315],
                                    ticktext=['N', 'NE', 'E', 'SE',
                                              'S', 'SW', 'W', 'NW'],
                                    direction="clockwise",
                                    rotation=90
                                )
                            ),
                            showlegend=True,
                            height=400
                        )

                        st.plotly_chart(fig_polar, use_container_width=True)
                    else:
                        st.warning(
                            "No wind data available for the selected flight.")
                else:
                    st.warning(
                        "No weather data available for wind direction analysis.")

            with wind_cols[1]:  # Add wind impact analysis in a 2x2 grid format
                if not wind_data.empty:
                    wind_impact = "favorable" if is_favorable else "unfavorable"
                    wind_angle_formatted = f"{wind_flight_angle:.1f}°"

                    # --- Define your box styles in a <style> block ---
                    st.markdown("""
                    <style>
                    .box {
                        background-color: white;
                        border-radius: 8px;
                        padding: 15px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
                        margin-bottom: 20px; /* Space under each box if you stack them */
                        height: 100%; /* Make all boxes the same height */
                    }
                    .box-title {
                        font-size: 16px;
                        color: #5B5B5B;
                        font-weight: 500;
                        margin-bottom: 5px;
                    }
                    .box-value {
                        font-size: 24px;
                        font-weight: 600;
                        margin-bottom: 5px;
                    }
                    .box-subtitle {
                        font-size: 14px;
                        color: #5B5B5B;
                    }
                    .favorable {
                        color: #34A853;
                    }
                    .unfavorable {
                        color: #EA4335;
                    }
                    </style>
                    """, unsafe_allow_html=True)

                    # Create two rows for the 2x2 grid
                    # First row
                    row1_col1, row1_col2 = st.columns(2, gap="medium")

                    # Second row
                    row2_col1, row2_col2 = st.columns(2, gap="medium")

                    # Place each info-box in its own column to create a 2x2 grid
                    with row1_col1:
                        st.markdown(f"""
                        <div class="box">
                            <div class="box-title">Flight Direction</div>
                            <div class="box-value">{flight_bearing:.1f}°</div>
                            <div class="box-subtitle">Where the flight is heading to</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with row1_col2:
                        st.markdown(f"""
                        <div class="box">
                            <div class="box-title">Wind Direction</div>
                            <div class="box-value">{avg_wind_dir:.1f}°</div>
                            <div class="box-subtitle">Where the wind is going to</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with row2_col1:
                        st.markdown(f"""
                        <div class="box">
                            <div class="box-title">Wind Speed</div>
                            <div class="box-value">{avg_wind_speed:.1f} knots</div>
                            <div class="box-subtitle">Average during flight time</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with row2_col2:
                        # Calculate estimated fuel impact and time impact based on wind conditions
                        if is_favorable:
                            fuel_impact = "Expected lower fuel consumption"
                            icon = "↗️"  # Up arrow for favorable
                        else:
                            fuel_impact = "Expected higher fuel consumption"
                            icon = "↘️"  # Down arrow for unfavorable

                        st.markdown(f"""
                        <div class="box">
                            <div class="box-title">Wind Impact</div>
                            <div class="box-value {wind_impact.lower()}">{wind_impact.capitalize()} {icon}</div>
                            <div class="box-subtitle">{fuel_impact}</div>
                        </div>
                        """, unsafe_allow_html=True)

        else:
            st.warning(
                "No route data available. Please select a departure and arrival airport, and date range.")

        st.markdown("</div>", unsafe_allow_html=True)

################

st.markdown("""
<div style="text-align:center; margin-top: 40px; padding: 20px; color: #6c757d;">
    <p>✈️ Flight Delay Analysis Dashboard | Data Engineering Project</p>
</div>
""", unsafe_allow_html=True)
