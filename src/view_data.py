import os
import duckdb

# Connect to the database
db_file = os.path.join(os.path.dirname(__file__), '..', 'toronto_environment.duckdb')
con = duckdb.connect(db_file)

print("--- TOP 5 ROWS: WEATHER ---")
# DuckDB makes it easy to view data using the .show() method
con.sql("SELECT * FROM raw_weather LIMIT 5").show()

print("\n--- TOP 5 ROWS: ALLERGIES ---")
con.sql("SELECT * FROM raw_allergy LIMIT 5").show()

print("\n--- LET'S JOIN THEM TOGETHER! ---")
# This is a sneak peek of what we will do with dbt!
con.sql("""
    SELECT 
        w.time,
        w.relative_humidity_2m as humidity,
        a.grass_pollen,
        a.ragweed_pollen
    FROM raw_weather w
    JOIN raw_allergy a ON w.time = a.time
    WHERE a.grass_pollen > 0
    LIMIT 5
""").show()

con.close()