import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', "flights_database.db")

st.set_page_config(
    page_title="NYC Flights Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="✈️"
)

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


def load_data(query):
    """Helper function to load data from the SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        df = pd.read_sql_query(query, conn)
    return df


st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 1rem;">
    <div style="flex: 5;">
        <h1>NYC Flights Dashboard ✈️</h1>
        <p>Welcome to the <strong>NYC Flights Dashboard</strong>. Explore flight data from New York City's major airports.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

nyc_airports = ('JFK', 'LGA', 'EWR')


#######################################################
# ALL QUERIES USED IN THE DASHBOARD
#######################################################

# QUERYING: total flights, percentage delayed, percentage missing arrival time
query_summary = """
SELECT 
    COUNT(*) as total_flights,
    ROUND(100.0 * SUM(CASE WHEN arr_delay > 0 THEN 1 ELSE 0 END) / 
          SUM(CASE WHEN arr_delay IS NOT NULL THEN 1 ELSE 0 END), 2) as delay_arrival_percentage,
    ROUND(100.0 * SUM(CASE WHEN arr_delay IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as missing_arrival_percentage
FROM flights
WHERE origin IN ('JFK','EWR','LGA');
"""

query_top_dest = """
    SELECT 
        dest, 
        COUNT(*) as flight_count,
        (SELECT name FROM airports WHERE faa = dest LIMIT 1) as dest_name
    FROM flights
    WHERE origin IN ('JFK','EWR','LGA')
    GROUP BY dest
    ORDER BY flight_count DESC
    LIMIT 1
    """

# QUERYING: top destination from NYC airports


def query_top_dest_from(airports):
    return f"""
    SELECT 
        dest, 
        COUNT(*) as flight_count,
        (SELECT name FROM airports WHERE faa = dest LIMIT 1) as dest_name
    FROM flights
    WHERE origin = {airport}
    GROUP BY dest
    ORDER BY flight_count DESC
    LIMIT 1
    """


# QUERYING: all routes from NYC airports
query_routes_all = """
    SELECT 
        origin, 
        dest, 
        COUNT(*) as flight_count
    FROM flights
    WHERE origin IN ('JFK', 'LGA', 'EWR')
    GROUP BY origin, dest
    """

# QUERYING: all routes from the chosen airport


def query_routes_from(airport):
    return f"""
    SELECT
        origin,
        dest,
        COUNT(*) as flight_count
    FROM flights
    WHERE origin = '{airport}'
    GROUP BY origin, dest
    """


def query_average_distances(airports):
    if type(airports) == str:
        return f"""
        SELECT 
            origin, 
            dest, 
            AVG(distance) as Distance
        FROM flights
        WHERE origin = '{airports}'
        GROUP BY dest
        """
    else:
        return f"""
        SELECT
            origin,
            dest,
            AVG(distance) as Distance   
        FROM flights
        WHERE origin IN {airports}
        GROUP BY origin, dest
        """


# QUERYING: all airports
query_airports = """
    SELECT 
        a.faa, a.name, a.lat, a.lon, 
        CAST(IFNULL(alt, 0) AS INTEGER) as Altitude,
        tz as Timezone
    FROM airports a
    """

airports_df = load_data(query_airports)
airports_df['is_nyc'] = airports_df['faa'].apply(
    lambda x: x in ['JFK', 'LGA', 'EWR']
)

# QUERYING: all routes from a specific airport
# pass airport as a tuple


def select_to_airport(airports):
    return f"""
        SELECT 
            origin, 
            dest, 
            COUNT(*) as flight_count
        FROM flights
        WHERE origin IN {airports}
        GROUP BY origin, dest
        """

# QUERYING: delay distribution from airport


def query_delay_distribution(airports):
    if type(airports) == str:
        return f"""
        SELECT 
            'On Time' as delay_category,
            COUNT(*) as flight_count,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights WHERE origin IN ('JFK','EWR','LGA') AND arr_delay IS NOT NULL), 2) as percentage
        FROM flights
        WHERE origin = '{airports}' AND arr_delay <= 0
        UNION ALL
        SELECT 
            'Minor (≤15 min)' as delay_category,
            COUNT(*) as flight_count,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights WHERE origin IN ('JFK','EWR','LGA') AND arr_delay IS NOT NULL), 2) as percentage
        FROM flights
        WHERE origin = '{airports}' AND arr_delay > 0 AND arr_delay <= 15
        UNION ALL
        SELECT 
            'Moderate (16-30 min)' as delay_category,
            COUNT(*) as flight_count,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights WHERE origin IN ('JFK','EWR','LGA') AND arr_delay IS NOT NULL), 2) as percentage
        FROM flights
        WHERE origin = '{airports}' AND arr_delay > 15 AND arr_delay <= 30
        UNION ALL
        SELECT 
            'Significant (31-60 min)' as delay_category,
            COUNT(*) as flight_count,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights WHERE origin IN ('JFK','EWR','LGA') AND arr_delay IS NOT NULL), 2) as percentage
        FROM flights
        WHERE origin = '{airports}' AND arr_delay > 30 AND arr_delay <= 60
        UNION ALL
        SELECT 
            'Severe (>60 min)' as delay_category,
            COUNT(*) as flight_count,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights WHERE origin IN ('JFK','EWR','LGA') AND arr_delay IS NOT NULL), 2) as percentage
        FROM flights
        WHERE origin = '{airports}' AND arr_delay > 60
        """
    else:
        return f"""
            SELECT 
                'On Time' as delay_category,
                COUNT(*) as flight_count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights WHERE origin IN ('JFK','EWR','LGA') AND arr_delay IS NOT NULL), 2) as percentage
            FROM flights
            WHERE origin IN {airports} AND arr_delay <= 0
            UNION ALL
            SELECT 
                'Minor (≤15 min)' as delay_category,
                COUNT(*) as flight_count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights WHERE origin IN ('JFK','EWR','LGA') AND arr_delay IS NOT NULL), 2) as percentage
            FROM flights
            WHERE origin IN {airports} AND arr_delay > 0 AND arr_delay <= 15
            UNION ALL
            SELECT 
                'Moderate (16-30 min)' as delay_category,
                COUNT(*) as flight_count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights WHERE origin IN ('JFK','EWR','LGA') AND arr_delay IS NOT NULL), 2) as percentage
            FROM flights
            WHERE origin IN {airports} AND arr_delay > 15 AND arr_delay <= 30
            UNION ALL
            SELECT 
                'Significant (31-60 min)' as delay_category,
                COUNT(*) as flight_count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights WHERE origin IN ('JFK','EWR','LGA') AND arr_delay IS NOT NULL), 2) as percentage
            FROM flights
            WHERE origin IN {airports} AND arr_delay > 30 AND arr_delay <= 60
            UNION ALL
            SELECT 
                'Severe (>60 min)' as delay_category,
                COUNT(*) as flight_count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flights WHERE origin IN ('JFK','EWR','LGA') AND arr_delay IS NOT NULL), 2) as percentage
            FROM flights
            WHERE origin IN {airports} AND arr_delay > 60
            """
# --------------------


df_summary = load_data(query_summary)

total_flights = int(df_summary['total_flights'][0])
delay_arrival_percentage = df_summary['delay_arrival_percentage'][0]
missing_arrival_percentage = df_summary['missing_arrival_percentage'][0]


df_top_dest = load_data(query_top_dest)
top_destination = df_top_dest['dest'][0]
top_dest_name = df_top_dest['dest_name'][0]
top_dest_count = int(df_top_dest['flight_count'][0])

col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">Total NYC Departures</div>
        <div class="metric-value">{:,} flights</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Delayed Arrivals</div>
        <div class="metric-value">{}%</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Most Popular Destination (2023)</div>
        <div class="metric-value">{} ({:,})</div>
        <div class="airport-subtitle">{}</div>
    </div>
    """.format(total_flights, delay_arrival_percentage, top_destination, top_dest_count, top_dest_name),
        unsafe_allow_html=True)


with col_right:
    # Create filters for airports and type of coloring
    col1, col2 = st.columns(2)

    with col1:
        all_airports_bool = st.toggle(
            "Show data for all origin airports", True)
        if not all_airports_bool:
            origin_airport = st.selectbox(
                "Select the origin airport", nyc_airports, index=0)
            routes_df = load_data(query_routes_from(origin_airport))
            airports_df_map = airports_df[airports_df['faa'].isin(
                routes_df['dest'].unique())]
            connected_airports = set(routes_df['dest'].unique())
            connected_airports.add(origin_airport)
            airports_df_map['has_connection'] = airports_df_map['faa'].apply(
                lambda x: x in connected_airports
            )
        else:
            origin_airport = nyc_airports
            airports_df_map = airports_df
            routes_df = load_data(query_routes_all)
            connected_airports = set(routes_df['dest'].unique())
            connected_airports.update(['JFK', 'LGA', 'EWR'])
            airports_df_map['has_connection'] = airports_df_map['faa'].apply(
                lambda x: x in connected_airports
            )

    with col2:
        color_by = st.selectbox(
            "Color by", ['Altitude', 'Distance', 'Timezone'])

    if color_by == 'Distance':
        airports_df_map = airports_df_map[airports_df_map['has_connection'] == True]

    average_distances = load_data(query_average_distances(origin_airport))
    airports_df_map = airports_df_map.merge(
        average_distances,
        how='left',
        left_on='faa',
        right_on='dest',
        suffixes=('', '_dest')
    )

    fig_map = px.scatter_geo(
        airports_df_map,
        lat='lat',
        lon='lon',
        hover_name='name',
        hover_data={
            'faa': True,
            'Altitude': True,
            'is_nyc': False,
            'has_connection': False,
            'lat': True,
            'lon': True,
            'Distance': True,
        },
        color=color_by,
        color_continuous_scale='Viridis',
        size_max=10,
        opacity=0.8,
        projection='albers usa'
    )

    fig_map.update_traces(
        marker=dict(
            size=airports_df_map.apply(
                lambda x: 20 if x['is_nyc'] else (
                    10 if x['has_connection'] else 5),
                axis=1
            ),
            line=dict(width=1, color='rgba(255, 255, 255, 0.5)')
        )
    )

    fig_map.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showland=True,
            landcolor='rgb(243, 243, 243)',
            countrycolor='rgb(204, 204, 204)',
            coastlinecolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(230, 230, 250)'
        ),
        height=400
    )

    st.markdown('<div>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center;">Destination ariports</h3>',
                unsafe_allow_html=True)
    st.plotly_chart(fig_map, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------
# Side-by-side charts: Delay Distribution and Airport Distribution
# ----------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Delay Distribution Overview")

    cola, colb = st.columns(2)

    with cola:
        all_airports_delays = st.toggle(
            "Show data for all origin airports", True, key='delay_dist')
        df_delay = load_data(query_delay_distribution(nyc_airports))
    with colb:
        if not all_airports_delays:
            airport = st.selectbox(
                "Select the origin airport", nyc_airports, index=0)
            df_delay = load_data(query_delay_distribution(airport))

    colors = ['#1B5E20', '#2E7D32', '#388E3C', '#43A047', '#66BB6A']

    fig_delay = px.bar(
        df_delay,
        x='delay_category',
        y='flight_count',
        text=df_delay['percentage'].apply(lambda x: f'{x}%'),
        color='delay_category',
        color_discrete_sequence=colors,
        labels={'flight_count': 'Number of Flights',
                'delay_category': 'Delay Category'},
        height=400
    )

    fig_delay.update_layout(
        xaxis_title='Delay Category',
        yaxis_title='Number of Flights',
        template='plotly_white',
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=80)
    )

    fig_delay.update_traces(
        textposition='inside',
        textfont=dict(size=14, color='white')
    )

    st.markdown('<div>', unsafe_allow_html=True)
    st.plotly_chart(fig_delay, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.subheader("Flight Volume by NYC Airport")

    query_airport_volume = """
    SELECT 
        origin as airport,
        CASE 
            WHEN origin = 'JFK' THEN 'John F. Kennedy (JFK)'
            WHEN origin = 'LGA' THEN 'LaGuardia (LGA)'
            WHEN origin = 'EWR' THEN 'Newark Liberty (EWR)'
        END as airport_name,
        COUNT(*) as flights_count,
        SUM(p.seats) as seats_sum,
        COUNT(DISTINCT f.dest) as destinations_count
    FROM flights f
    JOIN planes p ON f.tailnum = p.tailnum
    WHERE origin IN ('JFK','EWR','LGA')
    GROUP BY origin
    ORDER BY flights_count DESC
    """

    df_airports = load_data(query_airport_volume)

    flights_or_seats = st.selectbox("Show the distribution for total flights or total seats",
                                    ['Total Flights', 'Total Seats', 'Destinations served'], index=0)

    if flights_or_seats == 'Total Flights':
        data_col = 'flights_count'
    elif flights_or_seats == 'Total Seats':
        data_col = 'seats_sum'
    else:
        data_col = 'destinations_count'

    colors = ['#004D40', '#00796B', '#009688']

    fig_airports = px.pie(
        df_airports,
        names='airport_name',
        values=data_col,
        color_discrete_sequence=colors,
        hole=0.4,
        height=400
    )

    fig_airports.update_traces(
        textposition='inside',
        textinfo='label+percent',
        hoverinfo='label+value',
        textfont_size=14
    )

    fig_airports.update_layout(
        annotations=[dict(
            text=f"{df_airports[data_col].sum():,}<br>Flights",
            x=0.5, y=0.5,
            font_size=18,
            showarrow=False
        )],
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.markdown('<div>', unsafe_allow_html=True)
    st.plotly_chart(fig_airports, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------
# Top 10 Destinations Chart (Bar Chart)
# ----------------------------
st.subheader("Top 10 Destinations from NYC Airports")

query_top_destinations = """
SELECT 
    dest, 
    COUNT(*) as flight_count,
    (SELECT name FROM airports WHERE faa = dest LIMIT 1) as dest_name
FROM flights
WHERE origin IN ('JFK','EWR','LGA')
GROUP BY dest
ORDER BY flight_count DESC
LIMIT 10
"""
df_destinations = load_data(query_top_destinations)

green_palette = [
    "#f7fcf5",
    "#e5f5e0",
    "#d6efd0",
    "#c7e9c0",
    "#a1d99b",
    "#74c476",
    "#5ab769",
    "#41ab5d",
    "#238b45",
    "#006d2c",
    "#00441b"
]

fig_destinations = px.bar(
    df_destinations,
    y='dest',
    x='flight_count',
    color='flight_count',
    color_continuous_scale=green_palette,
    labels={'flight_count': 'Number of Flights',
            'dest': 'Destination Airport'},
    height=500,
    text=df_destinations['flight_count'],
    custom_data=['dest_name']
)

for i, row in enumerate(df_destinations.itertuples()):
    fig_destinations.add_annotation(
        x=0,
        y=row.dest,
        text=f"{row.dest_name}",
        showarrow=False,
        xshift=-10,
        align="right",
        xanchor="right",
        yanchor="middle",
        font=dict(size=10, color="gray"),
        opacity=0.8
    )

fig_destinations.update_traces(
    hovertemplate='<b>%{customdata[0]}</b> (%{y})<br>Number of Flights: %{x:,}<extra></extra>',
    texttemplate='%{x:,}',
    textposition='outside'
)

fig_destinations.update_layout(
    xaxis_title='Number of Flights',
    yaxis_title='',
    coloraxis_showscale=False,
    template='plotly_white',
    margin=dict(l=200, r=40, t=40, b=40)
)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.plotly_chart(fig_destinations, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# ----------------------------
# Airline Performance Analysis
# ----------------------------
st.subheader("Time of Day Analysis")
query_time_of_day = """
SELECT 
    CASE
        WHEN CAST(dep_time/100 AS INTEGER) BETWEEN 5 AND 8 THEN 'Early Morning (5-8)'
        WHEN CAST(dep_time/100 AS INTEGER) BETWEEN 9 AND 12 THEN 'Morning (9-12)'
        WHEN CAST(dep_time/100 AS INTEGER) BETWEEN 13 AND 16 THEN 'Afternoon (13-16)'
        WHEN CAST(dep_time/100 AS INTEGER) BETWEEN 17 AND 20 THEN 'Evening (17-20)'
        ELSE 'Night (21-4)'
    END as time_of_day,
    COUNT(*) as flight_count,
    ROUND(100.0 * SUM(CASE WHEN arr_delay > 0 THEN 1 ELSE 0 END) / 
        COUNT(CASE WHEN arr_delay IS NOT NULL THEN 1 ELSE NULL END), 2) as delay_percentage
FROM flights
WHERE origin IN ('JFK','EWR','LGA') AND dep_time IS NOT NULL
GROUP BY time_of_day
ORDER BY 
    CASE 
        WHEN time_of_day = 'Early Morning (5-8)' THEN 1
        WHEN time_of_day = 'Morning (9-12)' THEN 2
        WHEN time_of_day = 'Afternoon (13-16)' THEN 3
        WHEN time_of_day = 'Evening (17-20)' THEN 4
        ELSE 5
    END
"""
df_time = load_data(query_time_of_day)
green_colors = [
    "#a1d99b",
    "#74c476",
    "#5ab769",
    "#41ab5d",
    "#238b45",
]

fig_time = px.bar(
    df_time,
    x='time_of_day',
    y='delay_percentage',
    color='delay_percentage',
    color_continuous_scale=green_colors,
    text=df_time['delay_percentage'].apply(lambda x: f"{x}%"),
    labels={
        'time_of_day': 'Time of Day',
        'delay_percentage': 'Delayed Flights (%)'
    },
    height=450
)

fig_time.add_trace(
    go.Scatter(
        x=df_time['time_of_day'],
        y=df_time['flight_count'],
        mode='lines+markers',
        name='Flight Count',
        yaxis='y2',
        line=dict(color='rgba(0,0,0,0.7)', width=2),
        marker=dict(size=8)
    )
)

fig_time.update_layout(
    xaxis_title='Time of Day',
    yaxis_title='Delayed Flights (%)',
    yaxis2=dict(
        title='Number of Flights',
        overlaying='y',
        side='right'
    ),
    coloraxis_showscale=False,
    template='plotly_white',
    margin=dict(l=40, r=40, t=40, b=40),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)
fig_time.update_traces(
    textposition='inside',
    selector=dict(type='bar')
)

st.markdown('<div>', unsafe_allow_html=True)
st.plotly_chart(fig_time, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
