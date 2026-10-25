-- views.sql : bảng tổng hợp theo quận/huyện và tháng (chạy sau khi nạp dữ liệu)
-- Chỉ số Landsat chỉ tính trên ô có quan sát thật; NO2, CO, AOD, T2M, PRECIP tính trên mọi ô.
CREATE MATERIALIZED VIEW district_month AS
SELECT d.district_id,
       d.name_vi,
       o.obs_month,
       avg(o.lst)   FILTER (WHERE o.observed) AS lst,
       avg(o.ndvi)  FILTER (WHERE o.observed) AS ndvi,
       avg(o.tvdi)  FILTER (WHERE o.observed) AS tvdi,
       avg(o.utfvi) FILTER (WHERE o.observed) AS utfvi,
       avg(o.no2) AS no2,
       avg(o.co)  AS co,
       avg(o.aod) AS aod,
       avg(o.t2m) AS t2m,
       avg(o.precip) AS precip,
       count(*) FILTER (WHERE o.observed) AS n_observed,
       count(*) AS n_cells
FROM observation o
JOIN grid_cell c ON c.cell_id = o.cell_id
JOIN district d ON d.district_id = c.district_id
GROUP BY d.district_id, d.name_vi, o.obs_month;
CREATE UNIQUE INDEX idx_dm ON district_month (district_id, obs_month);