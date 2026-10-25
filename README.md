# WebGIS môi trường TP.HCM (Django + PostgreSQL/PostGIS)

Trực quan hóa và dự báo LST, NDVI, TVDI, UTFVI, NO₂, CO, AOD trên lưới 1 km (1.981 ô), 2020-01 đến 2026-08,
dự báo 9-12/2026. Dữ liệu xử lý trên Google Earth Engine; mô hình XGBoost (so sánh với Random Forest và khí hậu).

## Cấu trúc

```
dashboard_data/        dữ liệu đã đóng gói từ Colab (Cell 24)
postgres/              schema.sql, views.sql, load_to_postgres.py (nạp dữ liệu vào PostGIS)
webgis/                cấu hình Django
dashboard/
  api.py               các API JSON (SQL thuần, PostGIS trả GeoJSON)
  models.py            ánh xạ bảng có sẵn (managed = False)
  templates/, static/  giao diện Leaflet + Chart.js (thư viện để sẵn trong static/vendor, không cần CDN)
  management/commands/check_api.py   kiểm tra mọi API trên database thật
app.py                 bản mẫu Streamlit (dự phòng)
```

## Cách chạy (Windows, PowerShell)

1. PostgreSQL 16 trở lên có PostGIS. Mật khẩu để trong `%APPDATA%\postgresql\pgpass.conf`
   (dòng `localhost:5432:*:postgres:MAT_KHAU`) hoặc biến môi trường `DB_PASSWORD`; không ghi vào mã nguồn.
2. Tạo database UTF8:
   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -c "CREATE DATABASE env_hcm ENCODING 'UTF8' TEMPLATE template0;"
   ```
3. Cài thư viện và nạp dữ liệu:
   ```powershell
   py -3.13 -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   .venv\Scripts\python.exe postgres\load_to_postgres.py --db env_hcm --user postgres --data dashboard_data
   ```
4. Tạo bảng nội bộ của Django, kiểm tra và chạy:
   ```powershell
   .venv\Scripts\python.exe manage.py migrate
   .venv\Scripts\python.exe manage.py check_api
   .venv\Scripts\python.exe manage.py runserver
   ```
   Mở http://127.0.0.1:8000/ (Django Admin: `/admin/`, tạo tài khoản bằng `manage.py createsuperuser`).

Biến môi trường tùy chọn: `DB_NAME` (mặc định `env_hcm`), `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`,
`DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`0` khi triển khai).

## API

| Endpoint | Nội dung |
|---|---|
| `/api/health/` | phiên bản PostGIS, số dòng các bảng |
| `/api/meta/` | chỉ số, tháng lịch sử, tháng dự báo, quận, ghi chú |
| `/api/cells/`, `/api/districts/` | GeoJSON ô lưới và quận |
| `/api/values/?mode=history\|forecast&indicator=&month=YYYY-MM[&view=forecast\|climatology\|diff][&observed_only=1]` | giá trị theo ô |
| `/api/series/?indicator=&district=all\|id` | chuỗi theo tháng (Landsat: chỉ ô quan sát thật) |
| `/api/forecast/?indicator=&district=` | dự báo, khoảng dự báo, khí hậu, độ tin cậy |
| `/api/validation/?indicator=&district=` | kiểm thử 2026: thực tế, mô hình, khí hậu; RMSE, MAE, R² |
| `/api/ranking/?mode=&indicator=&month=[&view=]` | xếp hạng quận; UTFVI kèm tỉ lệ ô từ mức "Mạnh" |
| `/api/locate/?lon=&lat=` | quận chứa điểm (`ST_Contains`) |

Tham số sai trả mã 400 kèm thông báo.
