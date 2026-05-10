
  
    
    

    create  table
      "toronto_environment"."main_marts"."mart_daily_environment__dbt_tmp"
  
    as (
      with hourly as (
    select * from "toronto_environment"."main_staging"."stg_environment"
)

select
    observation_date,

    -- Humidity & Pressure
    round(avg(relative_humidity_2m)::numeric, 1) as avg_humidity_pct,
    round(avg(surface_pressure)::numeric,     1) as avg_pressure_hpa,

    -- Air Quality
    round(avg(pm2_5)::numeric, 1) as avg_pm2_5,
    round(max(pm2_5)::numeric, 1) as max_pm2_5,
    round(avg(pm10)::numeric,  1) as avg_pm10,
    round(max(pm10)::numeric,  1) as max_pm10,

    -- Pollen
    round(max(alder_pollen)::numeric,  0) as max_alder_pollen,
    round(max(birch_pollen)::numeric,  0) as max_birch_pollen,
    round(max(grass_pollen)::numeric,  0) as max_grass_pollen,
    round(max(ragweed_pollen)::numeric,0) as max_ragweed_pollen,

    count(*)             as hourly_records,
    max(observation_hour) as last_observation_hour

from hourly
group by observation_date
order by observation_date
    );
  
  