import os
import requests
import pandas as pd
import duckdb

# Toronto Coordinates
LATITUDE = 43.7001
LONGITUDE = -79.4163

def fetch_weather_data():
    """Fetches hourly humidity and pressure data for the past 7 days."""
    print("Fetching Weather Data (Humidity & Pressure)...")
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": ["relative_humidity_2m", "surface_pressure"],
        "past_days": 7,
        "timezone": "America/New_York"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status() # Check for errors
    data = response.json()
    
    # Open-Meteo returns data in a neat dictionary of lists. Pandas loves this.
    df = pd.DataFrame(data["hourly"])
    return df

def fetch_allergy_data():
    """Fetches hourly air quality and pollen (allergy) data for the past 7 days."""
    print("Fetching Air Quality & Pollen Data...")
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": ["pm10", "pm2_5", "alder_pollen", "birch_pollen", "grass_pollen", "ragweed_pollen"],
        "past_days": 7,
        "timezone": "America/New_York"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    df = pd.DataFrame(data["hourly"])
    return df

def load_to_duckdb(df_weather, df_allergy, db_path='toronto_environment.duckdb'):
    """Loads both DataFrames into separate raw tables in DuckDB."""
    print(f"Connecting to DuckDB at {db_path}...")
    con = duckdb.connect(db_path)
    
    # 1. Load Weather Data
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_weather (
            time VARCHAR,
            relative_humidity_2m DOUBLE,
            surface_pressure DOUBLE
        )
    """)
    print(f"Inserting {len(df_weather)} rows into raw_weather...")
    con.execute("INSERT INTO raw_weather SELECT * FROM df_weather")
    
    # 2. Load Allergy/Air Quality Data
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_allergy (
            time VARCHAR,
            pm10 DOUBLE,
            pm2_5 DOUBLE,
            alder_pollen DOUBLE,
            birch_pollen DOUBLE,
            grass_pollen DOUBLE,
            ragweed_pollen DOUBLE
        )
    """)
    print(f"Inserting {len(df_allergy)} rows into raw_allergy...")
    con.execute("INSERT INTO raw_allergy SELECT * FROM df_allergy")
    
    # Verify
    weather_count = con.execute("SELECT COUNT(*) FROM raw_weather").fetchone()[0]
    allergy_count = con.execute("SELECT COUNT(*) FROM raw_allergy").fetchone()[0]
    print(f"Success! Total rows in raw_weather: {weather_count}")
    print(f"Success! Total rows in raw_allergy: {allergy_count}")
    
    con.close()

if __name__ == "__main__":
    # 1. Extract
    df_weather = fetch_weather_data()
    df_allergy = fetch_allergy_data()
    
    # 2. Load
    db_file = os.path.join(os.path.dirname(__file__), '..', 'toronto_environment.duckdb')
    load_to_duckdb(df_weather, df_allergy, db_path=db_file)