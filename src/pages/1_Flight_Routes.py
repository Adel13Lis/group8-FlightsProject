import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
import os
import plotly.graph_objects as go
import plotly.express as px

DB_PATH =  os.path.join(os.path.dirname(__file__), '..', '..', "flights_database.db")

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

# Queries for weekly and monthly flight trends
query_weekly_trend = """
SELECT strftime('%W', date(year || '-' || month || '-' || day)) AS week_number, COUNT(*) AS flight_count
FROM flights
WHERE origin = '{origin}' AND dest = '{dest}'
GROUP BY week_number
ORDER BY week_number;
"""

query_monthly_trend = """
SELECT month, COUNT(*) AS flight_count
FROM flights
WHERE origin = '{origin}' AND dest = '{dest}'
GROUP BY month
ORDER BY month;
"""

def plot_weekly_trend(origin, dest):
    query_weekly_trend = f"""
    SELECT strftime('%w', date(year || '-' || month || '-' || day)) AS week_number, COUNT(*) AS flight_count
    FROM flights
    WHERE origin = '{origin}' AND dest = '{dest}'
    GROUP BY week_number
    ORDER BY week_number;
    """
    
    df_weekly = load_data(query_weekly_trend)

    if df_weekly.empty:
        st.warning("No weekly trend data available for this route.")
        return
    
    df_weekly = df_weekly.dropna(subset=["week_number"])
    df_weekly["week_number"] = df_weekly["week_number"].astype(int)

    weekday_labels = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    df_weekly["day_name"] = df_weekly["week_number"].apply(lambda x: weekday_labels[x] if 0 <= x <= 6 else "Unknown")

    df_weekly["day_name"] = pd.Categorical(df_weekly["day_name"], categories=weekday_labels, ordered=True)

    fig = px.line(df_weekly, x="day_name", y="flight_count", markers=True, 
                  title="Weekly Trend of Flights", labels={"day_name": "Day of the Week", "flight_count": "Number of Flights"})

    st.plotly_chart(fig, use_container_width=True)


def plot_monthly_trend(origin, dest):
    df_monthly = load_data(query_monthly_trend.format(origin=origin, dest=dest))

    if df_monthly.empty:
        st.warning("No monthly trend data available for this route.")
        return
    
    df_monthly = df_monthly.dropna(subset=["month"])
    df_monthly["month"] = df_monthly["month"].astype(int)

    month_labels = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"]
    df_monthly["month_name"] = df_monthly["month"].apply(lambda x: month_labels[x-1] if 1 <= x <= 12 else "Unknown")

    fig = px.line(df_monthly, x="month_name", y="flight_count", markers=True,
                  title="Monthly Trend of Flights", labels={"month_name": "Month", "flight_count": "Number of Flights"})

    st.plotly_chart(fig, use_container_width=True)

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

# Query flight statistics for this route
route_query = f"""
SELECT 
    COUNT(*) as flight_count,
    AVG(dep_delay) as avg_dep_delay,
    AVG(arr_delay) as avg_arr_delay,
    AVG(distance) as avg_distance
FROM flights
WHERE origin = '{origin}'
  AND dest = '{dest}';
"""
df_route_stats = load_data(route_query)

if df_route_stats.empty or df_route_stats['flight_count'][0] == 0:
    st.warning("No flights found for the selected route.")
else:
    flight_count = int(df_route_stats['flight_count'][0])
    avg_dep_delay = round(df_route_stats['avg_dep_delay'][0], 2)
    avg_arr_delay = round(df_route_stats['avg_arr_delay'][0], 2)
    avg_distance = round(df_route_stats['avg_distance'][0], 2)

    st.subheader("Route Statistics")
    
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Number of Flights</div>
            <div class="metric-value">{flight_count}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Avg. Departure Delay (min)</div>
            <div class="metric-value">{avg_dep_delay}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Avg. Arrival Delay (min)</div>
            <div class="metric-value">{avg_arr_delay}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Avg. Distance (miles)</div>
            <div class="metric-value">{avg_distance}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_right:
        st.markdown("<div>", unsafe_allow_html=True)
        st.subheader("Flight Route Map")

        # Query to fetch airport coordinates from the database
        route_query = f"""
        SELECT a1.lat AS origin_lat, a1.lon AS origin_lon, 
               a2.lat AS dest_lat, a2.lon AS dest_lon, 
            a2.tzone AS dest_tzone
        FROM airports a1
        JOIN airports a2 ON a1.faa = '{origin}' AND a2.faa = '{dest}'
        """
        route_data = load_data(route_query)

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
                    z=[0] * 50,  
                    colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,255,255,0)']],
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
                text=[origin, dest],
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

    st.markdown("---")
    
    # Maybe show a histogram of departure delays for this route
    hist_query = f"""
    SELECT dep_delay
    FROM flights
    WHERE origin = '{origin}' AND dest = '{dest}'
      AND dep_delay IS NOT NULL
    """
    df_hist = load_data(hist_query)

    if not df_hist.empty:
        chart = (
            alt.Chart(df_hist)
            .mark_bar(color="#4682B4")  # Updated to Steel Blue for better contrast
            .encode(
                alt.X("dep_delay:Q", bin=alt.Bin(maxbins=30),
                      title="Departure Delay (min)"),
                y='count()'
            )
            .properties(
                width=600,
                height=400,
                title="Distribution of Departure Delays"
            )
        )
        st.altair_chart(chart, use_container_width=True)

    st.markdown("---")
    
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    plot_weekly_trend(origin, dest)

with col2:
    plot_monthly_trend(origin, dest)


