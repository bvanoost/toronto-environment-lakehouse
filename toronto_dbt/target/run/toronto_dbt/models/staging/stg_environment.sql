
  
  create view "toronto_environment"."main_staging"."stg_environment__dbt_tmp" as (
    with weather_deduped as (
    select
        time_bucket(interval '1 hour', time::timestamptz) as observation_hour,
        relative_humidity_2m,
        surface_pressure,
        row_number() over (
            partition by time_bucket(interval '1 hour', time::timestamptz)
            order by time::timestamptz desc
        ) as rn
    from "toronto_environment"."main"."raw_weather"
    where time is not null
),

allergy_deduped as (
    select
        time_bucket(interval '1 hour', time::timestamptz) as observation_hour,
        pm2_5,
        pm10,
        alder_pollen,
        birch_pollen,
        grass_pollen,
        ragweed_pollen,
        row_number() over (
            partition by time_bucket(interval '1 hour', time::timestamptz)
            order by time::timestamptz desc
        ) as rn
    from "toronto_environment"."main"."raw_allergy"
    where time is not null
),

joined as (
    select
        w.observation_hour,
        date_trunc('day', w.observation_hour)   as observation_date,
        extract('hour' from w.observation_hour) as hour_of_day,

        -- Weather
        w.relative_humidity_2m,
        w.surface_pressure,

        -- Air quality
        a.pm2_5,
        a.pm10,

        -- Pollen
        a.alder_pollen,
        a.birch_pollen,
        a.grass_pollen,
        a.ragweed_pollen

    from weather_deduped w
    left join allergy_deduped a
        on  w.observation_hour = a.observation_hour
        and a.rn = 1
    where w.rn = 1
)

select * from joined
order by observation_hour
  );
