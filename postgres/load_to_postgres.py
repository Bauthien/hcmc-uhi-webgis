# load_to_postgres.py - nạp dashboard_data vào PostgreSQL/PostGIS
# Cách dùng (PowerShell):
#   python load_to_postgres.py --db env_hcm --user postgres --password MAT_KHAU --data dashboard_data
import argparse, io, json, os
import pandas as pd
import psycopg2

ap = argparse.ArgumentParser()
ap.add_argument('--host', default='localhost'); ap.add_argument('--port', default='5432')
ap.add_argument('--db', default='env_hcm'); ap.add_argument('--user', default='postgres')
ap.add_argument('--password', default=os.environ.get('PGPASSWORD', ''))
ap.add_argument('--data', default='dashboard_data')
ap.add_argument('--sql-dir', default=os.path.dirname(os.path.abspath(__file__)))
a = ap.parse_args()

DX, DY = 0.00457, 0.00452          # nửa cạnh ô 1 km tính theo độ kinh và vĩ (vĩ độ khoảng 10,8 độ)

def copy_df(cur, df, table, cols):
    buf = io.StringIO()
    df[cols].to_csv(buf, index=False, header=False, na_rep='')
    buf.seek(0)
    cur.copy_expert(f"COPY {table} ({','.join(cols)}) FROM STDIN WITH (FORMAT csv, NULL '')", buf)

for fn in ['cells.csv', 'history.csv.gz', 'forecast.csv.gz', 'test_2026.csv.gz', 'reliability.csv', 'meta.json']:
    if not os.path.exists(os.path.join(a.data, fn)):
        raise SystemExit(f'Không thấy file {fn} trong thư mục "{a.data}". Hãy giải nén dashboard_data.zip vào đó.')
conn = psycopg2.connect(host=a.host, port=a.port, dbname=a.db, user=a.user, password=a.password)
conn.set_client_encoding('UTF8')
conn.autocommit = False
cur = conn.cursor()
cur.execute('SHOW server_encoding')
enc = cur.fetchone()[0]
if enc.upper() != 'UTF8':
    raise SystemExit(f'Database "{a.db}" dùng mã hóa {enc}, không lưu được tiếng Việt. '
                     'Hãy tạo lại database trong pgAdmin với Encoding = UTF8 (tab Definition).')
print('Tạo bảng...')
cur.execute(open(os.path.join(a.sql_dir, 'schema.sql'), encoding='utf-8').read())

# ---- Quận/huyện và ô lưới ----
cells = pd.read_csv(f'{a.data}/cells.csv', encoding='utf-8-sig')
dist = cells.groupby('district_vi').size().rename('n_cells').reset_index().rename(columns={'district_vi': 'name_vi'})
copy_df(cur, dist, 'district', ['name_vi', 'n_cells'])
cur.execute('SELECT name_vi, district_id FROM district')
did = dict(cur.fetchall())
cells['district_id'] = cells.district_vi.map(did)
cur.execute('CREATE TEMP TABLE stg_cell (cell_id text, district_id int, lon double precision, lat double precision)')
copy_df(cur, cells, 'stg_cell', ['cell_id', 'district_id', 'lon', 'lat'])
cur.execute(f"""INSERT INTO grid_cell (cell_id, district_id, lon, lat, geom)
                SELECT cell_id, district_id, lon, lat, ST_MakeEnvelope(lon - {DX}, lat - {DY}, lon + {DX}, lat + {DY}, 4326)
                FROM stg_cell""")
# Ranh giới quận/huyện suy ra từ các ô lưới (đóng các khe hở nhỏ giữa ô)
cur.execute("""UPDATE district d SET geom = ST_Multi(ST_Buffer(ST_Buffer(g.u, 0.0008), -0.0008))
               FROM (SELECT district_id, ST_Union(geom) AS u FROM grid_cell GROUP BY district_id) g
               WHERE g.district_id = d.district_id""")
print('  quận/huyện:', len(dist), '| ô lưới:', len(cells))

# ---- Lịch sử ----
h = pd.read_csv(f'{a.data}/history.csv.gz', parse_dates=['date'], encoding='utf-8-sig')
h = h.rename(columns={'date': 'obs_month', 'LST': 'lst', 'NDVI': 'ndvi', 'TVDI': 'tvdi', 'UTFVI': 'utfvi',
                      'UTFVI_class': 'utfvi_class', 'NO2': 'no2', 'CO': 'co', 'AOD': 'aod'})
h['obs_month'] = h.obs_month.dt.date
h['utfvi_class'] = h.utfvi_class.astype('Int64')
copy_df(cur, h, 'observation', ['cell_id', 'obs_month', 'lst', 'ndvi', 'tvdi', 'utfvi', 'utfvi_class', 'no2', 'co', 'aod', 'observed'])
print('  observation:', len(h))

# ---- Dự báo ----
f = pd.read_csv(f'{a.data}/forecast.csv.gz', parse_dates=['date'], encoding='utf-8-sig')
f = f.rename(columns={'date': 'target_month', 'UTFVI_class': 'utfvi_class'})
f['target_month'] = f.target_month.dt.date
f['utfvi_class'] = f.utfvi_class.astype('Int64')
copy_df(cur, f, 'forecast', ['cell_id', 'indicator', 'target_month', 'horizon', 'forecast', 'lower', 'upper', 'climatology', 'utfvi_class'])
print('  forecast:', len(f))

# ---- Kiểm thử 2026 ----
t = pd.read_csv(f'{a.data}/test_2026.csv.gz', parse_dates=['date'], encoding='utf-8-sig').rename(columns={'date': 'obs_month'})
t['obs_month'] = t.obs_month.dt.date
copy_df(cur, t, 'validation_2026', ['cell_id', 'indicator', 'obs_month', 'actual', 'forecast', 'climatology'])
print('  validation_2026:', len(t))

# ---- Độ tin cậy và mô tả ----
r = pd.read_csv(f'{a.data}/reliability.csv', encoding='utf-8-sig')
copy_df(cur, r, 'reliability', ['indicator', 'horizon', 'rmse_model', 'rmse_climatology', 'vs_climatology_pct', 'err_q10', 'err_q90', 'reliability'])
meta = json.load(open(f'{a.data}/meta.json', encoding='utf-8'))
cur.execute('INSERT INTO app_meta (key, value) VALUES (%s, %s)', ('meta', json.dumps(meta, ensure_ascii=False)))

cur.execute(open(os.path.join(a.sql_dir, 'views.sql'), encoding='utf-8').read())
conn.commit()
cur.execute('ANALYZE')
conn.commit()

# ---- Kiểm tra nhanh ----
print('\nKiểm tra:')
for tb in ['district', 'grid_cell', 'observation', 'forecast', 'validation_2026', 'reliability', 'district_month']:
    cur.execute(f'SELECT count(*) FROM {tb}')
    print(f'  {tb:16s} {cur.fetchone()[0]:>9,} dòng')
cur.execute("SELECT name_vi, n_cells, ST_NumGeometries(geom), round(ST_Area(geom::geography)/1e6) FROM district ORDER BY n_cells DESC LIMIT 5")
print('  5 quận nhiều ô nhất (tên, số ô, số mảnh, diện tích km2):')
for row in cur.fetchall():
    print('   ', row)
cur.close(); conn.close()
print('\nXong.')