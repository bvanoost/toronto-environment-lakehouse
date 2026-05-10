# Toronto Environment Lakehouse

> A production-pattern **Data Lakehouse on a laptop** — hourly weather and air quality data for Toronto, flowing through a fully automated ELT pipeline into a live Streamlit dashboard.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-1.x-FFF000?logo=duckdb&logoColor=black)
![dbt](https://img.shields.io/badge/dbt-1.11-FF694B?logo=dbt&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What this project demonstrates

This project replicates the core patterns of a modern cloud data stack — **extract, load, transform, serve** — entirely on local infrastructure, with no paid services or API keys required.

| Pattern | Cloud equivalent | Implementation here |
|---|---|---|
| Object storage / raw zone | S3, GCS | DuckDB file — `raw_*` tables |
| Transformation layer | Spark, Snowflake | dbt-duckdb |
| Semantic / mart layer | dbt marts in warehouse | `main_marts` schema |
| BI / serving layer | Tableau, Looker | Streamlit |
| Orchestration | Airflow, Prefect | cron / shell script |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Open-Meteo APIs                 │
│        (Weather API + Air Quality API)           │
│              free · no key required              │
└────────────────────┬────────────────────────────┘
                     │  HTTP · hourly
                     ▼
┌─────────────────────────────────────────────────┐
│              src/extract.py                      │
│         requests · pandas · duckdb               │
│                                                  │
│  Fetches last 14 days of hourly data and         │
│  appends to raw tables in DuckDB                 │
└────────────────────┬────────────────────────────┘
                     │  INSERT INTO
                     ▼
┌─────────────────────────────────────────────────┐
│         toronto_environment.duckdb               │
│                                                  │
│   main.raw_weather    main.raw_allergy           │
│   ─────────────────   ───────────────────        │
│   time (VARCHAR)      time (VARCHAR)             │
│   relative_humidity   pm2_5                      │
│   surface_pressure    pm10                       │
│                       alder_pollen               │
│                       birch_pollen               │
│                       grass_pollen               │
│                       ragweed_pollen             │
└────────────────────┬────────────────────────────┘
                     │  dbt run
                     ▼
┌─────────────────────────────────────────────────┐
│              toronto_dbt/                        │
│                                                  │
│  staging/stg_environment          [VIEW]         │
│  ─────────────────────────────────────────────   │
│  · Casts time VARCHAR → timestamptz              │
│  · Deduplicates on observation_hour (ROW_NUMBER) │
│  · LEFT JOINs weather + air quality on hour      │
│  · 336 rows · one per hour                       │
│                                                  │
│  marts/mart_daily_environment     [TABLE]        │
│  ─────────────────────────────────────────────   │
│  · Aggregates hourly → one row per day           │
│  · avg/max PM2.5, PM10                           │
│  · avg humidity, pressure                        │
│  · max pollen counts                             │
│  · 14 rows                                       │
└────────────────────┬────────────────────────────┘
                     │  duckdb.connect()
                     ▼
┌─────────────────────────────────────────────────┐
│              src/app.py  (Streamlit)             │
│                                                  │
│  · Date-range filter sidebar                     │
│  · KPI cards — latest day at a glance            │
│  · Humidity trend · PM2.5 avg vs max             │
│  · Hourly PM2.5 · Pollen bar chart               │
│  · Raw data expander                             │
└─────────────────────────────────────────────────┘
```

---

## Project structure

```
trigger_tracker/
├── src/
│   ├── extract.py                  # EL script — hits APIs, loads DuckDB
│   └── app.py                      # Streamlit dashboard
├── toronto_dbt/
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/
│       │   ├── sources.yml         # declares raw_weather, raw_allergy
│       │   └── stg_environment.sql # cleans, dedupes, joins
│       └── marts/
│           ├── schema.yml          # column docs + dbt tests
│           └── mart_daily_environment.sql  # daily aggregates
├── toronto_environment.duckdb      # local lakehouse file
├── requirements.txt
└── README.md
```

---

## Quick start

### 1. Clone and set up the environment

```bash
git clone https://github.com/your-username/trigger-tracker.git
cd trigger_tracker

python3.12 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the extractor

```bash
python src/extract.py
```

Fetches the last 14 days of hourly weather and air quality data for Toronto from [Open-Meteo](https://open-meteo.com/) and loads it into `toronto_environment.duckdb`.

### 3. Configure dbt

Create `~/.dbt/profiles.yml`:

```yaml
toronto_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: /absolute/path/to/toronto_environment.duckdb
      threads: 4
```

### 4. Run dbt

```bash
cd toronto_dbt
dbt debug    # confirm connection
dbt run      # build staging view + daily mart table
dbt test     # run data quality tests
```

### 5. Launch the dashboard

```bash
cd ..
streamlit run src/app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## Data sources

| API | Endpoint | Fields extracted | Docs |
|---|---|---|---|
| Open-Meteo Weather | `/v1/forecast` | `relative_humidity_2m`, `surface_pressure` | [link](https://open-meteo.com/en/docs) |
| Open-Meteo Air Quality | `/v1/air-quality` | `pm2_5`, `pm10`, `alder_pollen`, `birch_pollen`, `grass_pollen`, `ragweed_pollen` | [link](https://open-meteo.com/en/docs/air-quality-api) |

- **Location**: Toronto, ON (43.70°N, 79.42°W)
- **Granularity**: Hourly
- **History**: 14 days rolling
- **Cost**: Free, no API key

---

## dbt model lineage

```
raw_weather  ──┐
               ├──▶  stg_environment  ──▶  mart_daily_environment
raw_allergy  ──┘
```

| Model | Schema | Type | Rows | Description |
|---|---|---|---|---|
| `stg_environment` | `main_staging` | View | ~336 | Cleaned, deduped, joined hourly data |
| `mart_daily_environment` | `main_marts` | Table | ~14 | One row per day, aggregated metrics |

---

## Requirements

```
requests
pandas
duckdb
dbt-duckdb
streamlit
```

Python 3.12 required. dbt-core does not support Python 3.14+.

---

## Roadmap

- [ ] Add temperature, precipitation, wind from Open-Meteo Weather API
- [ ] Cron job / shell script for automated daily refresh
- [ ] dbt `schema.yml` tests on all mart columns
- [ ] GitHub Actions CI to run `dbt test` on push
- [ ] Docker container for fully portable demo

---

## Author

**Brad Van Oost** · Senior Data Engineer  
