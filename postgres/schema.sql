-- schema.sql : cơ sở dữ liệu PostgreSQL/PostGIS cho đồ án (chạy bằng load_to_postgres.py hoặc dán vào pgAdmin Query Tool)
CREATE EXTENSION IF NOT EXISTS postgis;

DROP MATERIALIZED VIEW IF EXISTS district_month;
DROP TABLE IF EXISTS validation_2026, forecast, observation, grid_cell, district, reliability, app_meta CASCADE;

-- 22 quận/huyện (ranh giới suy ra từ các ô lưới; có thể thay bằng ranh giới GAUL chính xác sau)
CREATE TABLE district (
    district_id  serial PRIMARY KEY,
    name_vi      text UNIQUE NOT NULL,
    n_cells      integer,
    geom         geometry(MultiPolygon, 4326)
);

-- 1.981 ô lưới 1 km
CREATE TABLE grid_cell (
    cell_id      text PRIMARY KEY,
    district_id  integer NOT NULL REFERENCES district(district_id),
    lon          double precision NOT NULL,
    lat          double precision NOT NULL,
    geom         geometry(Polygon, 4326) NOT NULL
);
CREATE INDEX idx_cell_geom ON grid_cell USING GIST (geom);
CREATE INDEX idx_cell_district ON grid_cell (district_id);

-- Lịch sử theo ô và tháng (observed = giá trị Landsat là quan sát thật, false = đã nội suy)
CREATE TABLE observation (
    cell_id      text NOT NULL REFERENCES grid_cell(cell_id),
    obs_month    date NOT NULL,
    lst          real,
    ndvi         real,
    tvdi         real,
    utfvi        real,
    utfvi_class  smallint,
    no2          real,
    co           real,
    aod          real,
    observed     boolean,
    PRIMARY KEY (cell_id, obs_month)
);
CREATE INDEX idx_obs_month ON observation (obs_month);

-- Dự báo 9-12/2026 (horizon = số tháng dự báo trước)
CREATE TABLE forecast (
    cell_id       text NOT NULL REFERENCES grid_cell(cell_id),
    indicator     text NOT NULL,
    target_month  date NOT NULL,
    horizon       smallint NOT NULL,
    forecast      real,
    lower         real,
    upper         real,
    climatology   real,
    utfvi_class   smallint,
    PRIMARY KEY (cell_id, indicator, target_month)
);
CREATE INDEX idx_fc_ind_month ON forecast (indicator, target_month);

-- Kiểm thử 2026: thực tế so với dự báo trước 1 tháng
CREATE TABLE validation_2026 (
    cell_id      text NOT NULL REFERENCES grid_cell(cell_id),
    indicator    text NOT NULL,
    obs_month    date NOT NULL,
    actual       real,
    forecast     real,
    climatology  real,
    PRIMARY KEY (cell_id, indicator, obs_month)
);
CREATE INDEX idx_val_ind_month ON validation_2026 (indicator, obs_month);

CREATE TABLE reliability (
    indicator            text NOT NULL,
    horizon              smallint NOT NULL,
    rmse_model           real,
    rmse_climatology     real,
    vs_climatology_pct   real,
    err_q10              real,
    err_q90              real,
    reliability          text,
    PRIMARY KEY (indicator, horizon)
);

CREATE TABLE app_meta (key text PRIMARY KEY, value jsonb);