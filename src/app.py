import duckdb
import pandas as pd
import streamlit as st
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "toronto_environment.duckdb"

st.set_page_config(page_title="Toronto Environment", page_icon="🍁", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    daily  = con.execute("SELECT * FROM main_marts.mart_daily_environment ORDER BY observation_date").df()
    hourly = con.execute("SELECT * FROM main_staging.stg_environment ORDER BY observation_hour").df()
    con.close()
    daily["observation_date"]  = pd.to_datetime(daily["observation_date"], utc=True)
    hourly["observation_hour"] = pd.to_datetime(hourly["observation_hour"], utc=True)
    return daily, hourly

try:
    daily, hourly = load_data()
except Exception as e:
    st.error(f"Could not load data. Have you run `dbt run`?\n\n`{e}`")
    st.stop()

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("🍁 Toronto Environment")
st.sidebar.caption(f"{len(daily)} days of data loaded")

date_min = daily["observation_date"].min().date()
date_max = daily["observation_date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(date_min, date_max),
                                   min_value=date_min, max_value=date_max)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0], tz="UTC"), pd.Timestamp(date_range[1], tz="UTC")
else:
    start = end = pd.Timestamp(date_range[0], tz="UTC")

fd = daily[(daily["observation_date"] >= start) & (daily["observation_date"] <= end)]
fh = hourly[(hourly["observation_hour"] >= start) & (hourly["observation_hour"] <= end)]

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🌦 Toronto Weather & Air Quality")
st.caption(f"{len(fd)} days · {len(fh)} hourly observations")

# ── KPI cards ────────────────────────────────────────────────────────────────
if not fd.empty:
    latest = fd.iloc[-1]
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("💧 Avg Humidity",   f"{latest['avg_humidity_pct']} %")
    k2.metric("🌡 Avg Pressure",   f"{latest['avg_pressure_hpa']} hPa")
    k3.metric("🌫 Avg PM2.5",      f"{latest['avg_pm2_5']} µg/m³")
    k4.metric("🌫 Max PM2.5",      f"{latest['max_pm2_5']} µg/m³")
    k5.metric("📋 Hours recorded", f"{latest['hourly_records']}")

st.divider()

# ── Charts ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("💧 Humidity over time")
    if not fd.empty:
        st.line_chart(fd.set_index("observation_date")["avg_humidity_pct"])

with col2:
    st.subheader("🌫 PM2.5 — avg vs max")
    if not fd.empty:
        st.line_chart(fd.set_index("observation_date")[["avg_pm2_5", "max_pm2_5"]])

st.divider()

col3, col4 = st.columns(2)

with col3:
    st.subheader("🌿 Pollen — daily max")
    pollen_cols = ["max_alder_pollen", "max_birch_pollen", "max_grass_pollen", "max_ragweed_pollen"]
    pollen_data = fd.set_index("observation_date")[pollen_cols].dropna(how="all")
    if not pollen_data.empty:
        st.bar_chart(pollen_data.rename(columns=lambda c: c.replace("max_","").replace("_pollen","")))
    else:
        st.info("No pollen data yet — normal for this time of year.")

with col4:
    st.subheader("⏱ Hourly PM2.5")
    if not fh.empty:
        st.line_chart(fh.set_index("observation_hour")["pm2_5"])

st.divider()

with st.expander("📋 Daily summary table"):
    st.dataframe(fd.rename(columns=lambda c: c.replace("_"," ").title()),
                 use_container_width=True, hide_index=True)

st.caption("Data: [Open-Meteo](https://open-meteo.com/) · Free, no API key required")
