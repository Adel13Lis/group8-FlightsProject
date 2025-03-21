import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from geopy.distance import geodesic
import matplotlib.pyplot as plt
from timezonefinder import TimezoneFinder
import seaborn as sns
import math
import sqlite3
import numpy as np
from plotly.subplots import make_subplots
import datetime
from timezonefinder import TimezoneFinder
import pytz

# =============== Data processing for airports.csv ===============
# read airports.csv
df = pd.read_csv("../data/airports.csv")

# # descriptive statistics and data preprocessing
# print("first 5 rows of the dataset:\n", df.head())  # display first few rows
# print("dataset information:")
# df.info()  # display dataset information

# print("descriptive statistics:\n", df.describe())  # display descriptive statistics
# print("missing values in each column:\n", df.isnull().sum())  # check for missing values

# # display unique time zones and their corresponding tz values
# unique_tz_mapping = df[["tzone", "tz"]].dropna().drop_duplicates()
# print(unique_tz_mapping)

# inferring missing values instead of deleting them
tf = TimezoneFinder()
df["tzone"] = df.apply(
    lambda row: (
        tf.timezone_at(lng=row["lon"], lat=row["lat"])
        if pd.isnull(row["tzone"])
        else row["tzone"]
    ),
    axis=1,
)
# update tz values based on the inferred tzone
tz_mapping_dynamic = dict(
    df[["tzone", "tz"]].dropna().drop_duplicates().values)
df["tz"] = df.apply(
    lambda row: (
        tz_mapping_dynamic.get(row["tzone"], row["tz"])
        if pd.isnull(row["tz"])
        else row["tz"]
    ),
    axis=1,
)

# infer dst based on the most common dst setting per tzone


def infer_dst_from_tzone(tzone):
    if pd.isnull(tzone):
        return 'U'
    if "America/" in tzone:
        return 'A'
    elif "Europe/" in tzone:
        return 'E'
    else:
        return 'N'


df["dst"] = df.apply(
    lambda row: row["dst"] if pd.notnull(
        row["dst"]) else infer_dst_from_tzone(row["tzone"]),
    axis=1
)

# # check for missing values after inference
# print("missing values after inference:\n", df.isnull().sum())
# print(df[df["tz"].isnull()])
# print(df[df["tzone"] == "America/Boise"][["tzone", "tz"]].dropna().drop_duplicates()) # check for missing values in America/Boise
df.loc[df["tzone"] == "America/Boise", "tz"] = - \
    7  # fix missing values in America/Boise
# print("missing values after final fix:\n", df.isnull().sum())

df.loc[df['tz'] == 8, 'tz'] = -8  # fix incorrect tz value

# convert altitude to meters
df["alt_meters"] = df["alt"] * 0.3048
df["tz"] = df["tz"].astype("Int64")  # convert tz to integer
# df.info()

# explore relationships within the dataset
# print(df.describe()) # display descriptive statistics
# scatter plot: altitude vs latitude
plt.figure(figsize=(10, 6))
plt.scatter(df["lat"], df["alt_meters"], alpha=0.5, color="blue")

plt.xlabel("Latitude")
plt.ylabel("Altitude (meters)")
plt.title("Scatter Plot: Airport Altitude vs Latitude")
plt.grid(True)

# plt.show()

# print(df["dst"].unique()) # display unique values in 'dst' column
# print(df["tzone"].unique()) # display unique values in 'tzone' column
# print(df["tz"].unique()) # display unique values in 'tz' column

# countplot: number of airports in each time zone
plt.figure(figsize=(10, 6))
sns.countplot(x=df["tzone"], hue=df["tzone"], palette="coolwarm", legend=False)
# sns.countplot(x=df["tz"], hue=df["tz"], palette="coolwarm", legend=False)
plt.xlabel("Time Zone")
plt.xticks(rotation=25, ha='right', fontsize=6)
plt.ylabel("Number of Airports")
plt.title("Number of Airports in Each Time Zone")
plt.grid(True)
# plt.show()

# find airports that do not observe daylight saving time, later visualizing these airports on a map
df_no_dst = df[df["dst"] == "N"]

plt.figure(figsize=(10, 6))
sns.scatterplot(x=df_no_dst["lon"], y=df_no_dst["lat"], color="red")

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Airports That Do NOT Observe DST")

# plt.show()


# =============== Part 1,2 ===============
# visualizations
# plot global airport distribution, with color coded by 'alt' (altitude)
fig_global = px.scatter_geo(df,
                            lat="lat", lon="lon",
                            hover_name="name",
                            color="alt_meters",  # color by altitude
                            title="Global Airport Distribution (Colored by Altitude)",
                            projection="natural earth",
                            color_continuous_scale="Viridis",  # Choose color scale
                            # Set color legend title
                            labels={"alt_meters": "Altitude (m)"}
                            )

# fig_global.show()


# plot US airport distribution, with color coded by 'alt' (altitude)
# use scatter_geo funcion, scope="usa"
fig_us = px.scatter_geo(df,
                        lat="lat", lon="lon",
                        hover_name="name",
                        color="alt_meters",  # color by altitude
                        title="us airport distribution (colored by altitude)",
                        scope="usa",
                        color_continuous_scale="Viridis",
                        labels={"alt_meters": "Altitude (m)"}
                        )
# fig_us.show()

# analyze the distances between JFK and airports in the file
R = 6378.1370  # in kilometeres
jfk_data = df[df["faa"] == "JFK"]
jfk_loc = [jfk_data["lat"].iloc[0], jfk_data["lon"].iloc[0]]
df["geo_dist"] = None
df["euc_dist"] = None
for index, airport in df.iterrows():
    lat_scale = 111.32  # 1 degree of latitude ≈ 111.32 km
    lon_scale = 111.32 * math.cos(
        math.radians((airport["lat"] + jfk_loc[0]) / 2)
    )  # Adjust for longitude
    lat_diff_km = abs(airport["lat"] - jfk_loc[0]) * lat_scale
    lon_diff_km = abs(airport["lon"] - jfk_loc[1]) * lon_scale
    euc_distance = math.sqrt(lat_diff_km**2 + lon_diff_km**2)
    lat1 = math.radians(jfk_loc[0])
    lon1 = math.radians(jfk_loc[1])
    lat2 = math.radians(airport["lat"])
    lon2 = math.radians(airport["lon"])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    exp_one = (2 * math.sin(dlat / 2) * math.cos(dlon / 2)) ** 2
    exp_two = (2 * math.cos((lat1 + lat2) / 2) * math.sin(dlon / 2)) ** 2
    geo_distance = R * math.sqrt(exp_one + exp_two)
    # Store distances
    df.at[index, "euc_dist"] = euc_distance
    df.at[index, "geo_dist"] = geo_distance

# print(df.loc[df["euc_dist"].idxmax()])

plt.figure(figsize=(10, 6))
plt.hist(df["euc_dist"], bins=30, alpha=0.5, color="blue")

plt.xlabel("Euclidean distance")
plt.ylabel("Count")
plt.title("Distribution of the euclidean distances between the eirports and JFK")
plt.grid(True)

# plt.show()

plt.figure(figsize=(10, 6))
plt.hist(df["geo_dist"], bins=30, alpha=0.5, color="blue")

plt.xlabel("Geodesic distance")
plt.ylabel("Count")
plt.title("Distribution of the geodesic distances between the eirports and JFK")
plt.grid(True)

# plt.show()


def plot_multiple_flight_routes(faa_codes):
    nyc_airport = df[df["faa"] == "EWR"]
    if nyc_airport.empty:
        print("Error: No airport found for EWR.")
        return

    nyc_lat = nyc_airport["lat"].values[0]
    nyc_lon = nyc_airport["lon"].values[0]

    fig = px.scatter_geo(
        lat=[],
        lon=[],
        title="Flight Routes from NYC (EWR)",
        projection="natural earth",
    )

    for faa_code in faa_codes:
        airport = df[df["faa"] == faa_code.upper()]

        if airport.empty:
            print(f"Warning: No airport found with FAA code '{faa_code}'.")
            continue

        airport_name = airport["name"].values[0]
        airport_lat = airport["lat"].values[0]
        airport_lon = airport["lon"].values[0]
        airport_tzone = airport["tzone"].values[0]

        is_us = str(airport_tzone).startswith(("America/", "Pacific/"))

        fig.add_trace(
            go.Scattergeo(
                lon=[nyc_lon, airport_lon],
                lat=[nyc_lat, airport_lat],
                mode="lines",
                line=dict(width=2, color="blue"),
                name=f"NYC → {airport_name}",
            )
        )

        fig.add_trace(
            go.Scattergeo(
                lon=[airport_lon],
                lat=[airport_lat],
                text=[airport_name],
                mode="markers",
                marker=dict(size=8, color="green"),
                name=f"{airport_name}",
            )
        )

    fig.show()

# Example usage
# plot_multiple_flight_routes(["LAX", "JFK", "SFO", "AAF", "AAP"])


# Example Usage:
# plot_flight_route("LAX")
# plot_flight_route("HNL")  # the flight route line is broken
# plot_flight_route("TZR")


# =============== Data processing for flights_database.db ===============
# =============== Part 3 ===============
# verify the distances
# database_path
db_path = "../flights_database.db"

# transform calculate_geo_distance function to a function that can be used in SQL queries


def compute_geo_distance(lat1, lon1, lat2, lon2):
    R = 6378.1370
    # geo_distance
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    exp_one = (2 * math.sin(dlat / 2) * math.cos(dlon / 2)) ** 2
    exp_two = (2 * math.cos((lat1 + lat2) / 2) * math.sin(dlon / 2)) ** 2
    geo_distance = R * math.sqrt(exp_one + exp_two)
    return geo_distance


# connect to the database
with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()

    # query the first 200 flights with origin and destination airport coordinates
    cursor.execute("""
        SELECT f.origin, f.dest, f.distance, a1.lat, a1.lon, a2.lat, a2.lon
        FROM flights AS f
        JOIN airports AS a1 ON f.origin = a1.faa
        JOIN airports AS a2 ON f.dest = a2.faa
        LIMIT 200;
    """)
    flights_data = cursor.fetchall()

# calculate the geo and database distances for each flight
geo_distances = []
db_distances = []
indices = []

for i, (origin, dest, db_distance, lat1, lon1, lat2, lon2) in enumerate(flights_data):
    geo_distance = compute_geo_distance(lat1, lon1, lat2, lon2)
    geo_distances.append(geo_distance)
    db_distances.append(db_distance * 1.60934)  # convert miles to kilometers
    indices.append(i)

# plot the computed and database distances for the first 200 flights
plt.figure(figsize=(12, 6))
plt.plot(indices, geo_distances, label="Calculated Distance (km)", linestyle="-")
plt.plot(indices, db_distances, label="Database Distance (km)", linestyle="--")
plt.xlabel("Flight Index")
plt.ylabel("Distance (km)")
plt.title("Comparison of Computed vs. Database Flight Distances (First 200 Flights)")
plt.legend()
# plt.show()


# extract NYC airports
cursor.execute("""
    SELECT DISTINCT origin FROM flights;
""")
unique_origins = [row[0] for row in cursor.fetchall()]

query = f"""
    SELECT * FROM airports
    WHERE faa IN ({', '.join(['?'] * len(unique_origins))});
    """
df_unique_origins = pd.read_sql_query(query, conn, params=unique_origins)

# print(df_unique_origins)
conn.close()

# analyse flights per day
# retrieve the number of flights per day for a specific NYC airport


def plot_flight_destinations(month, day, airport):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # query the number of flights to each destination from the specified airport
        cursor.execute("""
            SELECT dest, COUNT(*) AS flight_count
            FROM flights
            WHERE month = ? AND day = ? AND origin = ?
            GROUP BY dest
            ORDER BY flight_count DESC;
        """, (month, day, airport))

        results = cursor.fetchall()

    destinations = [row[0] for row in results]
    flight_counts = [row[1] for row in results]

    plt.figure(figsize=(12, 6))
    plt.bar(destinations, flight_counts, color="skyblue")
    plt.xlabel("Destination Airport")
    plt.ylabel("Number of Flights")
    plt.title(f"Flights from {airport} on {month}/{day}")
    plt.xticks(rotation=90)
    plt.show()


# plot_flight_destinations(1, 1, "JFK")  # plot the flight destinations for JFK on January 1st
conn.close()

# retrieve flight statistics


def get_flight_statistics(month, day, airport):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # statistics for total flights
        cursor.execute("""
            SELECT COUNT(*) FROM flights
            WHERE month = ? AND day = ? AND origin = ?;
        """, (month, day, airport))
        total_flights = cursor.fetchone()[0]

        # statistics for unique destinations
        cursor.execute("""
            SELECT COUNT(DISTINCT dest) FROM flights
            WHERE month = ? AND day = ? AND origin = ?;
        """, (month, day, airport))
        unique_destinations = cursor.fetchone()[0]

        # find the most visited destination
        cursor.execute("""
            SELECT dest, COUNT(*) AS flight_count
            FROM flights
            WHERE month = ? AND day = ? AND origin = ?
            GROUP BY dest
            ORDER BY flight_count DESC
            LIMIT 1;
        """, (month, day, airport))
        most_visited = cursor.fetchone()

        statistics = {
            "total_flights": total_flights,
            "unique_destinations": unique_destinations,
            "most_visited": most_visited[0] if most_visited else None,
            "most_visited_count": most_visited[1] if most_visited else 0
        }

    return statistics


# get flight statistics for JFK on January 1st
stats = get_flight_statistics(1, 1, "JFK")
# print(stats)
# conn.close()


def average_delay_per_carrier_plot():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # query the number of flights to each destination from the specified airport
        cursor.execute("""SELECT AVG(f.dep_delay), f.carrier, al.name 
            FROM flights f 
            JOIN airlines al ON f.carrier = al.carrier 
            GROUP BY f.carrier""")

        results = cursor.fetchall()

    plt.figure(figsize=(12, 6))
    plt.bar([x[2] for x in results], [x[0] for x in results], color="skyblue")
    plt.xlabel("Airlines")
    plt.ylabel("Average delay")
    plt.title("Average delay for each airline")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.show()
    conn.close()

# average_delay_per_carrier_plot()


def delays_month_destination(months, destination):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        query = f"""
        SELECT COUNT(*)
        FROM flights
        WHERE dest = '{destination}' AND month IN {months} AND arr_delay > 0
        """
        results = conn.execute(query).fetchone()[0]
    conn.close()
    return results

# print(delays_month_destination((1,2,3), 'ORD'))


def bins_distance_delay():
    conn = sqlite3.connect(db_path)
    # Define the bins
    bins = range(0, 3001, 200)

    # Query the database
    query = """
    SELECT distance, arr_delay
    FROM flights
    """
    df = pd.read_sql_query(query, conn)

    # Bin the distances
    df['distance_bins'] = pd.cut(df['distance'], bins)

    # Group by the bins and calculate the mean arrival delay
    grouped = df.groupby('distance_bins')['arr_delay'].mean().reset_index()

    # Extract the midpoint of each bin for plotting
    grouped['bin_midpoint'] = grouped['distance_bins'].apply(lambda x: x.mid)

    # Plot the scatter plot
    plt.scatter(grouped['bin_midpoint'], grouped['arr_delay'])
    plt.xlabel('Distance Bin Midpoint')
    plt.ylabel('Average Arrival Delay')
    plt.title('Average Arrival Delay by Distance Bin')
    plt.grid(True)
    plt.show()
    conn.close()

# bins_distance_delay()


def bins_distance_delay_per_carrier():
    conn = sqlite3.connect(db_path)
    # Define the bins
    bins = range(0, 3001, 200)

    # Query the database
    query = """
    SELECT distance, arr_delay, carrier
    FROM flights
    """
    df = pd.read_sql_query(query, conn)

    # Bin the distances
    df['distance_bins'] = pd.cut(df['distance'], bins)

    # Group by both distance_bins and carrier, and calculate the mean arrival delay
    grouped = df.groupby(['distance_bins', 'carrier'])[
        'arr_delay'].mean().reset_index()

    # Extract the midpoint of each bin for plotting
    grouped['bin_midpoint'] = grouped['distance_bins'].apply(lambda x: x.mid)

    # Filter carriers with at least 10 bins with data
    non_missing_counts = grouped.groupby('carrier')['arr_delay'].apply(
        lambda x: x.notna().sum()).reset_index(name='n_non_missing')
    filtered_carriers = non_missing_counts[non_missing_counts['n_non_missing'] >= 10]['carrier']

    # Filter the original DataFrame to include only the selected carriers
    grouped_filtered = grouped[grouped['carrier'].isin(filtered_carriers)]

    # Get the list of filtered carriers
    carriers = grouped_filtered['carrier'].unique()

    # Determine the grid size for subplots
    n_carriers = len(carriers)
    n_cols = 3  # Number of columns in the grid
    n_rows = (n_carriers // n_cols) + (1 if n_carriers % n_cols != 0 else 0)

    # Create a grid of subplots
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, n_rows * 3))
    axes = axes.flatten()  # Flatten the 2D array of axes for easy iteration

    # Plot a line plot for each filtered carrier in its own subplot
    for i, carrier in enumerate(carriers):
        ax = axes[i]
        carrier_data = grouped_filtered[grouped_filtered['carrier'] == carrier]
        ax.plot(carrier_data['bin_midpoint'],
                carrier_data['arr_delay'], marker='o', label=carrier)
        ax.set_title(f'Carrier: {carrier}')
        ax.set_xlabel('Distance Bin Midpoint')
        ax.set_ylabel('Average Arrival Delay')
        ax.grid(True)
        ax.legend()

    # Hide any unused subplots
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    plt.tight_layout()  # Adjust layout to prevent overlap
    plt.show()
    conn.close()

# bins_distance_delay_per_carrier()


def top_manufacturers_to_destiantion(destination):
    with sqlite3.connect(db_path) as conn:
        query = f"""
            SELECT manufacturer, COUNT(*) AS num_flights
            FROM (
                SELECT tailnum
                FROM flights
                WHERE dest = '{destination}'
            ) f
            JOIN (
                SELECT manufacturer, tailnum
                FROM planes
            ) p
            ON f.tailnum = p.tailnum
            GROUP BY manufacturer
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """
        df = pd.read_sql(query, conn).set_index("manufacturer")

    plt.figure(figsize=(12, 6))
    plt.bar(df.index, df["num_flights"], color="skyblue")
    plt.xlabel("Manufacturer")
    plt.ylabel("Number of Flights")
    plt.title(f"Top 5 Manufacturers for Destination {destination}")
    plt.show()
    conn.close()

# top_manufacturers_to_destiantion("ATL")

# returns a dict describing how many times each plane type was used for flight trajectory between origin and destination flight


def flights_between_cities(origin, destination):
    ny_airports = {"JFK", "LGA", "EWR"}
    with sqlite3.connect(db_path) as conn:
        if origin not in ny_airports:
            raise ValueError("Origin airport must be from a New York.")

        query = f"""
            SELECT COUNT(*) AS count
            FROM airports
            WHERE faa = '{destination}'
        """
        if pd.read_sql(query, conn).iloc[0, 0] == 0:
            raise ValueError("Destination airport is not the database.")

        query = f"""
            SELECT type, COUNT(*) AS num_flights
            FROM (
                SELECT tailnum
                FROM flights
                WHERE dest = '{destination}'
                AND origin = '{origin}'
            ) f
            JOIN (
                SELECT type, tailnum
                FROM planes
            ) p
            ON f.tailnum = p.tailnum
            GROUP BY type
        """

        return pd.read_sql(query, conn).set_index("type")
    conn.close()

# print(flights_between_cities("JFK", "ATL").to_dict()["num_flights"])


# GROUP BY `tailnum` the flights and compute for each of them the average speed.
# Add the avg. speed to the `planes`
def compute_avg_speed_and_update_db():
    with sqlite3.connect(db_path) as conn:
        query_tailnum = """
            SELECT tailnum, AVG(distance*1.0/air_time) AS avg_speed
            FROM flights
            WHERE air_time > 0
            GROUP BY tailnum
        """

        tailnum_speed_df = pd.read_sql_query(query_tailnum, conn)
        tailnum_speed_df['avg_speed'] = tailnum_speed_df['avg_speed'].round(2)

        print(tailnum_speed_df)

        cur = conn.cursor()
        for _, row in tailnum_speed_df.iterrows():
            # cur.execute("UPDATE planes SET speed = ? WHERE tailnum = ?",
            #             (row['avg_speed'], row['tailnum']))
            print(
                f"UPDATE planes SET speed = {row['avg_speed']} WHERE tailnum = {row['tailnum']}")


# compute_avg_speed_and_update_db()


# Computation of the flying direction (bearing) from New York to destination
# airport. Then compute the inner product between flight direction and wind direction.
def inner_product_angle(angle1, angle2):
    """
    Returns a scalar value between -1 and 1.
    """
    # Convert degrees to radians
    rad1 = math.radians(angle1)
    rad2 = math.radians(angle2)

    # Dot product of two unit vectors in 2D:
    #   (sin(rad1), cos(rad1)) dot (sin(rad2), cos(rad2))
    # = sin(rad1)*sin(rad2) + cos(rad1)*cos(rad2)
    # = cos(rad1 - rad2)
    return math.cos(rad1 - rad2)


def calculate_compass_bearing(pointA, pointB):
    """
    Calculates the bearing between two points.

    Parameters:
        pointA: tuple of (latitude, longitude) in decimal degrees for the start point.
        pointB: tuple of (latitude, longitude) in decimal degrees for the destination.

    Returns:
        The bearing in degrees (from north being 0°).
    """
    lat1, lon1 = pointA
    lat2, lon2 = pointB

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    diff_long = math.radians(lon2 - lon1)

    x = math.sin(diff_long) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * \
        math.cos(lat2) * math.cos(diff_long)

    initial_bearing = math.atan2(x, y)

    initial_bearing = math.degrees(initial_bearing)

    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


# Example case: Compute bearing angle between Amsterdam and Berlin.
# Amsterdam Schiphol Airport: (52.3105, 4.7683)
# Berlin Brandenburg Airport: (52.366667, 13.503333)
# schiphol = (52.3105, 4.7683)
# berlin = (52.366667, 13.503333)

# bearing = calculate_compass_bearing(schiphol, berlin)
# print(
#     f"The initial bearing from Schiphol Airport to Berlin Brandenburg Airport is {bearing:.1f}°")

def generate_bearing_df():
    with sqlite3.connect(db_path) as conn:
        query_flights = "SELECT flight, origin, dest, time_hour FROM flights"
        query_weather = "SELECT origin, wind_dir, time_hour FROM weather"
        query_airports = "SELECT faa, lat, lon FROM airports"

        cur = conn.cursor()

        cur.execute(query_flights)
        rows_flights = cur.fetchall()
        df_flights = pd.DataFrame(rows_flights, columns=[
                                  x[0] for x in cur.description])

        cur.execute(query_weather)
        rows_weather = cur.fetchall()
        df_weather = pd.DataFrame(rows_weather, columns=[
                                  x[0] for x in cur.description])

        cur.execute(query_airports)
        rows_airports = cur.fetchall()
        df_airports = pd.DataFrame(rows_airports, columns=[
                                   x[0] for x in cur.description])

        # 1) Merge df_flights and df_weather on origin/time_hour
        df_flights = pd.merge(
            df_flights,
            df_weather,
            on=["origin", "time_hour"],
            how="inner"
        )

        # 2) Merge with df_airports to get lat/lon for the origin airport
        df_flights = pd.merge(
            df_flights,
            df_airports[["faa", "lat", "lon"]],
            left_on="origin",
            right_on="faa",
            how="left"
        )
        df_flights.rename(
            columns={"lat": "lat_origin", "lon": "lon_origin"}, inplace=True)
        df_flights.drop("faa", axis=1, inplace=True)

        # 3) Merge with df_airports to get lat/lon for the destination airport
        df_flights = pd.merge(
            df_flights,
            df_airports[["faa", "lat", "lon"]],
            left_on="dest",
            right_on="faa",
            how="left"
        )
        df_flights.rename(
            columns={"lat": "lat_dest", "lon": "lon_dest"}, inplace=True)
        df_flights.drop("faa", axis=1, inplace=True)

        bearings = []
        inner_products = []

        for _, row in df_flights.iterrows():
            origin_coords = (row['lat_origin'], row['lon_origin'])
            dest_coords = (row['lat_dest'], row['lon_dest'])
            bearing = calculate_compass_bearing(origin_coords, dest_coords)
            bearings.append(bearing)

        df_flights['bearing'] = bearings

        for _, row in df_flights.iterrows():
            ip = inner_product_angle(row['wind_dir'], row['bearing'])
            inner_products.append('positive' if ip >= 0 else 'negative')

        df_flights['innerProd'] = inner_products

    # Return the constructed DataFrame instead of an empty string
    return df_flights


# Example case
df_flights_bearing = generate_bearing_df()
df_flights_bearing_small = df_flights_bearing.copy().dropna().head(5)
# print(df_flights_bearing_small)

# Example case: Show polar histogram ofthe first 5 pairs of directions to see if the inner product is affected by the direction of the plane (in air) and direction of the wind.
for idx, row in df_flights_bearing_small.iterrows():
    # Create 1x2 subplot layout
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "polar"}, {"type": "polar"}]],
        # these become annotations
        subplot_titles=("Wind Direction", "Bearing")
    )

    # First polar histogram (Wind Direction)
    fig.add_trace(
        go.Barpolar(
            r=[1],
            theta=[row["wind_dir"]],
            name="Wind Dir"
        ),
        row=1, col=1
    )

    # Second polar histogram (Bearing)
    fig.add_trace(
        go.Barpolar(
            r=[1],
            theta=[row["bearing"]],
            name="Bearing"
        ),
        row=1, col=2
    )

    # Adjust layout (including the main figure title if you want)
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 1.2], showticklabels=False, ticks="")
        ),
        polar2=dict(
            radialaxis=dict(range=[0, 1.2], showticklabels=False, ticks="")
        ),
        showlegend=False,
        title={
            "text": f"From {row['origin']} to {row['dest']}. I.P. {row['innerProd']}",
            "x": 0.5,
            "y": 0.95
        },
        margin=dict(t=100)
    )

    # Move each subplot title (annotation) higher
    # Increase the y-value as needed (e.g., +0.04, +0.05, etc.)
    for annotation in fig.layout.annotations:
        annotation.y += 0.05

    # fig.show()


# =============== Part 4 ===============
def compute_air_time(sched_dep, sched_arr):
    # Convert scheduled times to 4-digit strings (e.g., 530 -> "0530")
    dep_str = f"{int(sched_dep):04d}"
    arr_str = f"{int(sched_arr):04d}"

    # Parse the time strings into datetime objects (using an arbitrary common date)
    dep_time = datetime.datetime.strptime(dep_str, "%H%M")
    arr_time = datetime.datetime.strptime(arr_str, "%H%M")

    # If arrival time is earlier than departure time, assume the flight crossed midnight
    if arr_time < dep_time:
        arr_time += datetime.timedelta(days=1)

    # Calculate the difference in minutes
    return (arr_time - dep_time).seconds / 60


# Missing values handling
with sqlite3.connect(db_path) as conn:
    df_flights = pd.read_sql_query("SELECT * FROM flights", conn)

# Check missing values before filling
missing_counts = df_flights.isnull().sum()
# print("Flights table missing values before filling:", missing_counts)

# Fill missing values in 'dep_time' and 'arr_time' with 'sched_dep_time' and 'sched_arr_time'
df_flights['dep_time'] = df_flights['dep_time'].fillna(
    df_flights['sched_dep_time'])
df_flights['arr_time'] = df_flights['arr_time'].fillna(
    df_flights['sched_arr_time'])

# Fill missing values in 'dep_delay' and 'arr_delay' with 0 (assuming missing indicates no delay)
df_flights['dep_delay'] = df_flights['dep_delay'].fillna(0)
df_flights['arr_delay'] = df_flights['arr_delay'].fillna(0)

# Fill missing values in 'tailnum' with "Unknown"
df_flights['tailnum'] = df_flights['tailnum'].fillna("Unknown")

# Fill missing values in 'air_time' using the computed difference from scheduled times
df_flights['air_time'] = df_flights.apply(
    lambda row: compute_air_time(row['sched_dep_time'], row['sched_arr_time'])
    if pd.isnull(row['air_time']) else row['air_time'],
    axis=1
)
conn.close()

# Check missing values after filling
# print("Flights table missing values after filling:", df_flights.isnull().sum())

# find duplicate_flights


def find_duplicate_flights():
    with sqlite3.connect(db_path) as conn:
        query = """
            SELECT year, month, day, origin, dest, sched_dep_time,carrier,tailnum , COUNT(*) AS duplicate_count
            FROM flights
            GROUP BY year, month, day, origin, dest, sched_dep_time, carrier,tailnum
            HAVING duplicate_count > 1;
        """
        duplicates = pd.read_sql_query(query, conn)
    return duplicates


duplicate_flights = find_duplicate_flights()
# print("Duplicate flights:", duplicate_flights)
# prin duplicate flights 2023-1-10 JFK BOS 840 YX N725MQ
# print(df_flights[(df_flights['year'] == 2023) & (df_flights['month'] == 1) & (df_flights['day'] == 10) & (df_flights['origin'] == 'JFK') & (df_flights['dest'] == 'BOS')& (df_flights['sched_dep_time'] == 840) & (df_flights['carrier'] == 'YX')])

# covert to datetime objects


def flights_with_dtime_objects():
    def parse_dtime(year, month, day, num):
        # If the time value is missing, return a missing value indicator.
        if pd.isna(num):
            return pd.NA

        # If the time is 2400, consider it as midnight of the next day.
        if num == 2400:
            return datetime.datetime(year=year, month=month, day=day) + datetime.timedelta(days=1)

        # Split the number into hours and minutes.
        hours, minutes = divmod(num, 100)

        return datetime.datetime(year=year, month=month, day=day, hour=int(hours % 24), minute=int(minutes))

    # Connect to the database and load the flights table
    with sqlite3.connect(db_path) as conn:
        query = "SELECT * FROM flights"
        flights = pd.read_sql(query, conn)

    # Convert time columns to datetime objects using the helper function
    flights["dep_time"] = flights.apply(lambda row: parse_dtime(
        row["year"], row["month"], row["day"], row["dep_time"]), axis=1)
    flights["sched_dep_time"] = flights.apply(lambda row: parse_dtime(
        row["year"], row["month"], row["day"], row["sched_dep_time"]), axis=1)
    flights["arr_time"] = flights.apply(lambda row: parse_dtime(
        row["year"], row["month"], row["day"], row["arr_time"]), axis=1)
    flights["sched_arr_time"] = flights.apply(lambda row: parse_dtime(
        row["year"], row["month"], row["day"], row["sched_arr_time"]), axis=1)

    # Convert delay and air_time fields into timedelta objects
    flights["dep_delay"] = flights["dep_delay"].apply(
        lambda delay: datetime.timedelta(minutes=delay) if not pd.isna(delay) else pd.NA)
    flights["arr_delay"] = flights["arr_delay"].apply(
        lambda delay: datetime.timedelta(minutes=delay) if not pd.isna(delay) else pd.NA)
    flights["air_time"] = flights["air_time"].apply(lambda air_time: datetime.timedelta(
        minutes=air_time) if not pd.isna(air_time) else pd.NA)

    return flights


# Example usage:
df_with_dtime = flights_with_dtime_objects()
# print(df_with_dtime.head())

#####################################################################
# Checking whether the dat in flights is in order (Part 4)
#####################################################################
with sqlite3.connect('../flights_database.db') as conn:
    df = pd.read_sql('SELECT * FROM flights', conn)

df = df.copy()

fix_count = {
    'dep_time': 0, 'dep_delay': 0, 'arr_time': 0, 'arr_delay': 0, 'air_time': 0
}


def hhmm_to_minutes(hhmm):
    """Convert HHMM time format to total minutes since midnight."""
    if pd.isna(hhmm) or hhmm < 0:
        return None
    hh = hhmm // 100
    mm = hhmm % 100
    return hh * 60 + mm


def minutes_to_hhmm(minutes):
    """Convert total minutes since midnight back to HHMM format, handling midnight wrap."""
    if pd.isna(minutes) or minutes < 0:
        return None
    minutes = minutes % 1440  # Ensure time does not exceed 23:59
    hh = minutes // 60
    mm = minutes % 60
    return hh * 100 + mm if hh > 0 else mm


def fix_times_if_else(df, time_col, sched_col, delay_col):
    """Fix missing or incorrect departure and arrival times."""
    for index, row in df.iterrows():
        time = row[time_col]
        sched_time = row[sched_col]
        delay = row[delay_col]

        time = hhmm_to_minutes(time) if pd.notna(time) else None
        sched_time = hhmm_to_minutes(sched_time)
        delay = int(delay) if pd.notna(delay) else None

        # 1. If all three values exist, ignore the row
        if time is not None and sched_time is not None and delay is not None:
            continue

        # 2. If time is missing but sched_time and delay exist
        elif time is None and sched_time is not None and delay is not None:
            df.at[index, time_col] = minutes_to_hhmm(sched_time + delay)
            fix_count[time_col] += 1

        # 3. If delay is missing but sched_time and time exist
        elif delay is None and sched_time is not None and time is not None:
            df.at[index, delay_col] = (time - sched_time) % 1440
            fix_count[delay_col] += 1

        # 4. If both time and delay are missing, use sched_time
        elif time is None and delay is None and sched_time is not None:
            df.at[index, time_col] = minutes_to_hhmm(sched_time)
            df.at[index, delay_col] = 0
            fix_count[time_col] += 1
            fix_count[delay_col] += 1


def fix_air_time(df):
    """Fix incorrect or missing air_time values."""
    for index, row in df.iterrows():
        dep_time = hhmm_to_minutes(row['dep_time'])
        arr_time = hhmm_to_minutes(row['arr_time'])
        air_time = row['air_time']

        # 1. If all three values exist, ignore the row
        if dep_time is not None and arr_time is not None and pd.notna(air_time):
            if int(air_time) == (arr_time - dep_time) % 1440:
                continue

        # 2. If air_time is incorrect or missing, fix it
        if dep_time is not None and arr_time is not None:
            df.at[index, 'air_time'] = (arr_time - dep_time) % 1440
            fix_count['air_time'] += 1


fix_times_if_else(df, 'dep_time', 'sched_dep_time', 'dep_delay')
fix_times_if_else(df, 'arr_time', 'sched_arr_time', 'arr_delay')

fix_air_time(df)

# # ADDITIONAL PART : ADD THE UPDATED TIMES TO THE FLIGHTS DATABASE


def add_updated_times_to_db():
    conn = sqlite3.connect('/content/flights_database.db')
    conn.execute("PRAGMA busy_timeout = 30000")
    cur = conn.cursor()

    unique_time_hours = df['time_hour'].unique().tolist()
    unique_flights = df['flight'].unique().tolist()

    select_all_query = f"""
    SELECT time_hour, flight, dep_time, sched_dep_time, dep_delay, arr_time, sched_arr_time, arr_delay, air_time
    FROM flights
    WHERE time_hour IN ({','.join('?'*len(unique_time_hours))})
    AND flight IN ({','.join('?'*len(unique_flights))})
    """
    params = unique_time_hours + unique_flights
    cur.execute(select_all_query, params)
    rows = cur.fetchall()

    flights_dict = {(r[0], r[1]): r[2:] for r in rows}

    update_queries = []

    for row in df.itertuples(index=False):
        key = (row.time_hour, row.flight)
        if key in flights_dict:
            current_values = flights_dict[key]
            if any(value is None or value == "" for value in current_values):
                update_query = f"""
                    UPDATE flights
                    SET dep_time = '{row.dep_time}',
                        sched_dep_time = '{row.sched_dep_time}',
                        dep_delay = '{row.dep_delay}',
                        arr_time = '{row.arr_time}',
                        sched_arr_time = '{row.sched_arr_time}',
                        arr_delay = '{row.arr_delay}',
                        air_time = '{row.air_time}'
                    WHERE time_hour = '{row.time_hour}' AND flight = '{row.flight}';
                    """
                update_queries.append(update_query)

    conn.close()

    # Database was open a second time, because of a persisting 'database is locked' error.
    conn = sqlite3.connect('/content/flights_database.db')
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    update_script = "\n".join(update_queries)

    try:
        # Execute all updates in one go.
        conn.executescript(update_script)
        conn.commit()
        print("All updates executed successfully.")
    except Exception as e:
        conn.rollback()
        print("Error during batch update:", e)
    finally:
        conn.close()

# add_updated_times_to_db()


############################################
# GENERATE THE COLUMN local_arr_time that represents the arrival time of the plane at local time
############################################
def find_tzone_from_coords():
    '''The function takes the rows with empty tzones and uses the coordinates to find the tzone and insert back to the table'''
    con = sqlite3.connect(db_path)

    airports_df = pd.read_sql("SELECT * FROM airports", con)

    print(airports_df.isna().sum())

    tf = TimezoneFinder()

    for idx, row in airports_df[airports_df['tzone'].isnull()].iterrows():
        lat = row['lat']
        lon = row['lon']

        if pd.isnull(lat) or pd.isnull(lon):
            continue

        found_tzone = tf.timezone_at(lng=lon, lat=lat)

        if found_tzone:
            airports_df.at[idx, 'tzone'] = found_tzone
        else:
            pass

    airports_df.to_sql('airports', con, if_exists='replace', index=False)

    con.close()

# find_tzone_from_coords()


def convert_to_local_time(row):
    try:
        if pd.isnull(row["arr_time"]) or pd.isnull(row["tzone"]):
            return None

        ny_tz = pytz.timezone("America/New_York")
        dest_tz = pytz.timezone(row["tzone"])

        ny_time_hhmm = int(row["arr_time"])
        hour = ny_time_hhmm // 100
        minute = ny_time_hhmm % 100

        if hour >= 24:
            hour -= 24
            new_date = datetime.datetime(row["year"], row["month"],
                                         row["day"]) + datetime.timedelta(days=1)
        else:
            new_date = datetime.datetime(row["year"], row["month"], row["day"])

        ny_time = ny_tz.localize(
            datetime.datetime(new_date.year, new_date.month, new_date.day, hour, minute))
        local_time = ny_time.astimezone(dest_tz)

        return local_time.hour * 100 + local_time.minute

    except Exception as e:
        print(f"Error processing row {row.name}: {e}")
        return None


con = sqlite3.connect(db_path)

airports_df = pd.read_sql("SELECT faa, lat, lon, tzone FROM airports", con)
flights_df = pd.read_sql(
    "SELECT year, month, day, arr_time, dest FROM flights", con)

merged_df = flights_df.merge(
    airports_df, left_on="dest", right_on="faa", how="left")

merged_df = merged_df.dropna(subset=["lat", "lon"])

merged_df = merged_df.reset_index(drop=True)

merged_df["local_arr_time"] = merged_df.apply(convert_to_local_time, axis=1)

con.close()
# merged_df.head(10)
