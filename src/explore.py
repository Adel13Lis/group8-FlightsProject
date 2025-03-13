import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def load_data(query):
    """Helper function to load data from the SQLite database."""
    with sqlite3.connect("/Users/monika/projectFlights-group8-1/flights_database.db") as conn:
        cursor = conn.cursor()
        df = pd.read_sql_query(query, conn)
    return df

query_all_airports = """
SELECT *
FROM airports
""" 

query_all_destinations = """
SELECT DISTINCT(dest)
FROM flights
"""

query_airports = """
    SELECT 
        a.faa, a.name, a.lat, a.lon, 
        CAST(IFNULL(alt, 0) AS INTEGER) as Altitude
    FROM airports a
    JOIN flights f ON a.faa = f.dest
    GROUP BY a.faa
    """

query_airports_right = """
    SELECT 
        a.faa, a.name, a.lat, a.lon, 
        CAST(IFNULL(alt, 0) AS INTEGER) as Altitude
    FROM airports a
    RIGHT JOIN flights f ON a.faa = f.dest
    GROUP BY a.faa
    """

query_routes_all = """
    SELECT 
        origin, 
        dest, 
        COUNT(*) as flight_count
    FROM flights
    WHERE origin IN ('JFK', 'LGA', 'EWR')
    GROUP BY origin, dest
    """

airports_df = load_data(query_airports)

routes_df = load_data(query_routes_all)
connected_airports = set(routes_df['dest'].unique())

print(len(connected_airports))
connected_airports.update(['JFK', 'LGA', 'EWR'])
airports_df['has_connection'] = airports_df['faa'].apply(
    lambda x: x in connected_airports
)

print(airports_df[airports_df['has_connection'] == True].size)

print(load_data(query_all_airports).size)
print(load_data(query_all_destinations).size)
print(load_data(query_airports)['faa'].unique().size)
print(load_data(query_airports_right)['faa'].unique().size)

# find the airport not in the airports table
print(set(load_data(query_all_destinations)['dest']) - set(load_data(query_airports)['faa']))
print(set(load_data(query_all_destinations)['dest']) - set(load_data(query_airports_right)['faa']))


