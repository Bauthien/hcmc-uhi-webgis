# api.py - các endpoint JSON của WebGIS (đặc tả ở mục 9c file bàn giao).
# Truy vấn bằng SQL thuần qua connection.cursor(); tên cột chỉ lấy từ danh sách trắng INDICATORS,
# giá trị người dùng luôn truyền qua tham số %s (không ghép chuỗi), nên tránh được SQL injection.
import json
import math
import re
from datetime import date
from functools import wraps

from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

# Thứ tự hiển thị; col = tên cột trong bảng observation và district_month
INDICATORS = {
    'UTFVI': {'col': 'utfvi', 'name': 'Chỉ số sinh thái nhiệt (UTFVI)', 'unit': '', 'landsat': True, 'decimals': 4},
    'LST': {'col': 'lst', 'name': 'Nhiệt độ bề mặt (LST)', 'unit': '°C', 'landsat': True, 'decimals': 1},
    'NDVI': {'col': 'ndvi', 'name': 'Chỉ số thực vật (NDVI)', 'unit': '', 'landsat': True, 'decimals': 3},
    'TVDI': {'col': 'tvdi', 'name': 'Chỉ số hạn khô (TVDI)', 'unit': '', 'landsat': True, 'decimals': 3},
    'NO2': {'col': 'no2', 'name': 'NO₂ tầng đối lưu', 'unit': 'µmol/m²', 'landsat': False, 'decimals': 1},
    'CO': {'col': 'co', 'name': 'CO', 'unit': 'mmol/m²', 'landsat': False, 'decimals': 1},
    'AOD': {'col': 'aod', 'name': 'Độ dày quang học sol khí (AOD)', 'unit': '', 'landsat': False, 'decimals': 3},
}
FORECAST_VIEWS = ('forecast', 'climatology', 'diff')
STRONG_UTFVI_CLASS = 4          # từ mức "Mạnh" trở lên
SMALL_DISTRICT_CELLS = 10       # quận dưới 10 ô: trung bình kém tin cậy
CACHE_SECONDS = 3600


class ParamError(Exception):
    pass


def api(view):
    """Chỉ nhận GET; lỗi tham số trả JSON 400."""
    @require_GET
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except ParamError as e:
            return JsonResponse({'error': str(e)}, status=400)
    return wrapper


def rows(sql, params=()):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def scalar(sql, params=()):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()[0]


def ym(d):
    return d.strftime('%Y-%m')


def rnd(v, decimals):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return round(float(v), decimals)


# ---------------- Dữ liệu ít thay đổi (đệm trong bộ nhớ) ----------------
def app_meta():
    # Django tắt việc psycopg2 tự giải mã jsonb nên giá trị về dạng chuỗi
    def load():
        v = scalar("SELECT value FROM app_meta WHERE key = 'meta'")
        return json.loads(v) if isinstance(v, str) else (v or {})
    return cache.get_or_set('app_meta', load, CACHE_SECONDS)


def history_months():
    return cache.get_or_set('history_months', lambda: [
        r['obs_month'] for r in rows('SELECT DISTINCT obs_month FROM observation ORDER BY 1')], CACHE_SECONDS)


def forecast_months():
    """{tháng: horizon}"""
    return cache.get_or_set('forecast_months', lambda: {
        r['target_month']: r['horizon']
        for r in rows('SELECT DISTINCT target_month, horizon FROM forecast ORDER BY 1')}, CACHE_SECONDS)


def districts():
    return cache.get_or_set('districts', lambda: rows(
        'SELECT district_id, name_vi, n_cells FROM district ORDER BY name_vi'), CACHE_SECONDS)


def history_range(ind):
    """Phân vị 2% và 98% trên toàn bộ lịch sử (chỉ số Landsat: chỉ ô quan sát thật), để thang màu cố định."""
    spec = INDICATORS[ind]
    where = 'WHERE observed' if spec['landsat'] else ''

    def compute():
        lo, hi = scalar(f"SELECT percentile_cont(ARRAY[0.02, 0.98]) WITHIN GROUP (ORDER BY {spec['col']}) "
                        f"FROM observation {where}")
        return [lo, hi]
    return cache.get_or_set(f'range_{ind}', compute, CACHE_SECONDS)


def classify_utfvi(v):
    """Mức UTFVI 1..6 theo ngưỡng trong app_meta: <=0 là 1, (0; 0,005] là 2, ..., >0,02 là 6."""
    if v is None:
        return None
    k = 1
    for t in app_meta().get('utfvi_thresholds', [0, 0.005, 0.01, 0.015, 0.02]):
        if v > t:
            k += 1
    return k


# ---------------- Đọc và kiểm tra tham số ----------------
def p_indicator(request):
    ind = request.GET.get('indicator', '').upper()
    if ind not in INDICATORS:
        raise ParamError(f'indicator phải là một trong: {", ".join(INDICATORS)}')
    return ind


def p_mode(request):
    mode = request.GET.get('mode', 'history')
    if mode not in ('history', 'forecast'):
        raise ParamError('mode phải là history hoặc forecast')
    return mode


def p_month(request, allowed):
    s = request.GET.get('month', '')
    m = re.fullmatch(r'(\d{4})-(\d{2})', s)
    if not m:
        raise ParamError('month phải có dạng YYYY-MM')
    d = date(int(m.group(1)), int(m.group(2)), 1) if 1 <= int(m.group(2)) <= 12 else None
    if d not in allowed:
        raise ParamError(f'Không có dữ liệu cho tháng {s}')
    return d


def p_view(request):
    view = request.GET.get('view', 'forecast')
    if view not in FORECAST_VIEWS:
        raise ParamError(f'view phải là một trong: {", ".join(FORECAST_VIEWS)}')
    return view


def p_district(request):
    s = request.GET.get('district', 'all')
    if s == 'all':
        return None
    if not s.isdigit() or int(s) not in {d['district_id'] for d in districts()}:
        raise ParamError('district phải là "all" hoặc district_id hợp lệ')
    return int(s)


def p_flag(request, name):
    return request.GET.get(name, '0') in ('1', 'true', 'yes')


def reliability_rows(ind, horizon=None):
    sql = ('SELECT horizon, rmse_model, rmse_climatology, vs_climatology_pct, err_q10, err_q90, reliability '
           'FROM reliability WHERE indicator = %s')
    params = [ind]
    if horizon is not None:
        sql += ' AND horizon = %s'
        params.append(horizon)
    return rows(sql + ' ORDER BY horizon', params)


# ---------------- Endpoint ----------------
@api
def health(request):
    counts = {t: scalar(f'SELECT count(*) FROM {t}') for t in
              ('district', 'grid_cell', 'observation', 'forecast', 'validation_2026', 'reliability', 'district_month')}
    return JsonResponse({'postgis': scalar('SELECT postgis_lib_version()'),
                         'postgresql': scalar('SHOW server_version'), 'rows': counts})


@api
def meta(request):
    m = app_meta()
    return JsonResponse({
        'indicators': [{'id': k, 'name': v['name'], 'unit': v['unit'], 'landsat': v['landsat'],
                        'decimals': v['decimals']} for k, v in INDICATORS.items()],
        'history_months': [ym(d) for d in history_months()],
        'forecast_months': [{'month': ym(d), 'horizon': h} for d, h in forecast_months().items()],
        'districts': [{'id': d['district_id'], 'name': d['name_vi'], 'n_cells': d['n_cells']} for d in districts()],
        'small_district_cells': SMALL_DISTRICT_CELLS,
        'meta': m,
    })


def geojson_response(cache_key, sql):
    text = cache.get_or_set(cache_key, lambda: scalar(sql), CACHE_SECONDS)
    return HttpResponse(text, content_type='application/geo+json; charset=utf-8')


@api
def cells(request):
    return geojson_response('geo_cells', """
        SELECT json_build_object('type', 'FeatureCollection', 'features', json_agg(json_build_object(
                   'type', 'Feature',
                   'geometry', ST_AsGeoJSON(c.geom, 5)::json,
                   'properties', json_build_object('cell_id', c.cell_id, 'district_id', c.district_id,
                                                   'district', d.name_vi)) ORDER BY c.cell_id))::text
        FROM grid_cell c JOIN district d USING (district_id)""")


@api
def district_shapes(request):
    return geojson_response('geo_districts', """
        SELECT json_build_object('type', 'FeatureCollection', 'features', json_agg(json_build_object(
                   'type', 'Feature',
                   'geometry', ST_AsGeoJSON(geom, 5)::json,
                   'properties', json_build_object('district_id', district_id, 'name', name_vi,
                                                   'n_cells', n_cells)) ORDER BY name_vi))::text
        FROM district""")


def month_values(mode, ind, month, view, observed_only):
    """Giá trị theo ô của một tháng: danh sách (cell_id, giá trị, mức UTFVI)."""
    spec = INDICATORS[ind]
    out = []
    if mode == 'history':
        for r in rows(f"SELECT cell_id, {spec['col']} AS v, utfvi_class AS k, observed "
                      f"FROM observation WHERE obs_month = %s", [month]):
            if observed_only and spec['landsat'] and not r['observed']:
                continue
            out.append((r['cell_id'], r['v'], r['k'] if ind == 'UTFVI' else None))
    else:
        for r in rows('SELECT cell_id, forecast, climatology, utfvi_class FROM forecast '
                      'WHERE indicator = %s AND target_month = %s', [ind, month]):
            if view == 'forecast':
                out.append((r['cell_id'], r['forecast'], r['utfvi_class'] if ind == 'UTFVI' else None))
            elif view == 'climatology':
                out.append((r['cell_id'], r['climatology'],
                            classify_utfvi(r['climatology']) if ind == 'UTFVI' else None))
            elif r['forecast'] is not None and r['climatology'] is not None:
                out.append((r['cell_id'], r['forecast'] - r['climatology'], None))
    return [x for x in out if x[1] is not None]


@api
def values(request):
    mode, ind = p_mode(request), p_indicator(request)
    spec = INDICATORS[ind]
    month = p_month(request, history_months() if mode == 'history' else forecast_months())
    view = p_view(request) if mode == 'forecast' else None
    observed_only = p_flag(request, 'observed_only')
    data = month_values(mode, ind, month, view, observed_only)

    if view == 'diff':
        diffs = sorted(abs(v) for _, v, _ in data)
        half = diffs[int(0.98 * (len(diffs) - 1))] if diffs else 0
        value_range, diverging = [-half, half], True
    else:
        value_range, diverging = history_range(ind), False

    dec = spec['decimals'] + 2
    resp = {
        'mode': mode, 'indicator': ind, 'month': ym(month), 'view': view,
        'name': spec['name'], 'unit': spec['unit'], 'decimals': spec['decimals'],
        'values': {c: rnd(v, dec) for c, v, _ in data},
        'classes': {c: k for c, _, k in data if k is not None} if ind == 'UTFVI' and view != 'diff' else None,
        'range': [rnd(x, dec) for x in value_range], 'diverging': diverging,
        'n_cells': len(data),
        'landsat_missing': spec['landsat'] and mode == 'history' and ym(month) in app_meta().get(
            'months_without_landsat', []),
    }
    if mode == 'forecast':
        resp['horizon'] = forecast_months()[month]
        rel = reliability_rows(ind, resp['horizon'])
        resp['reliability'] = rel[0] if rel else None
    return JsonResponse(resp)


def series_data(ind, district_id):
    """Chuỗi theo tháng của toàn thành phố và (nếu có) của một quận. Landsat: chỉ ô quan sát thật."""
    spec = INDICATORS[ind]
    col = spec['col']
    agg = f'avg({col}) FILTER (WHERE observed)' if spec['landsat'] else f'avg({col})'
    city = rows(f'SELECT obs_month, {agg} AS v, count(*) FILTER (WHERE observed) AS n_obs, count(*) AS n '
                f'FROM observation GROUP BY obs_month ORDER BY obs_month')
    dec = spec['decimals'] + 2
    out = {'months': [ym(r['obs_month']) for r in city],
           'city': [rnd(r['v'], dec) for r in city],
           'city_n_observed': [r['n_obs'] for r in city] if spec['landsat'] else None,
           'district': None, 'district_n_observed': None}
    if district_id is not None:
        # district_month (materialized view) đã lọc ô quan sát thật cho chỉ số Landsat
        dm = {r['obs_month']: r for r in rows(
            f'SELECT obs_month, {col} AS v, n_observed FROM district_month WHERE district_id = %s', [district_id])}
        out['district'] = [rnd(dm[m]['v'], dec) if m in dm else None for m in history_months()]
        if spec['landsat']:
            out['district_n_observed'] = [dm[m]['n_observed'] if m in dm else 0 for m in history_months()]
    return out


@api
def series(request):
    ind, district_id = p_indicator(request), p_district(request)
    spec = INDICATORS[ind]
    out = series_data(ind, district_id)
    out.update({'indicator': ind, 'name': spec['name'], 'unit': spec['unit'], 'decimals': spec['decimals'],
                'district_id': district_id,
                'months_without_landsat': app_meta().get('months_without_landsat', []) if spec['landsat'] else []})
    return JsonResponse(out)


def district_filter(district_id, alias):
    """Đoạn JOIN/WHERE lọc theo quận; trả (sql_join, sql_where, params)."""
    if district_id is None:
        return '', '', []
    return f'JOIN grid_cell c ON c.cell_id = {alias}.cell_id', 'AND c.district_id = %s', [district_id]


@api
def forecast(request):
    ind, district_id = p_indicator(request), p_district(request)
    spec = INDICATORS[ind]
    join, where, params = district_filter(district_id, 'f')
    fc = rows(f'SELECT f.target_month, f.horizon, avg(f.forecast) AS forecast, avg(f.lower) AS lower, '
              f'avg(f.upper) AS upper, avg(f.climatology) AS climatology '
              f'FROM forecast f {join} WHERE f.indicator = %s {where} '
              f'GROUP BY f.target_month, f.horizon ORDER BY f.target_month', [ind] + params)
    hist = series_data(ind, district_id)
    key = 'district' if district_id is not None else 'city'
    dec = spec['decimals'] + 2
    return JsonResponse({
        'indicator': ind, 'name': spec['name'], 'unit': spec['unit'], 'decimals': spec['decimals'],
        'district_id': district_id,
        'forecast': [{'month': ym(r['target_month']), 'horizon': r['horizon'],
                      **{k: rnd(r[k], dec) for k in ('forecast', 'lower', 'upper', 'climatology')}} for r in fc],
        'history': {'months': hist['months'][-24:], 'values': hist[key][-24:]},
        'reliability': reliability_rows(ind),
        'interval_note': 'Khoảng dự báo là trung bình của khoảng theo từng ô (phân vị 10% và 90% của sai số '
                         'theo ô ở kiểm thử 2026, chỉ 8 tháng), nên rộng hơn sai số của giá trị trung bình.',
    })


@api
def validation(request):
    ind, district_id = p_indicator(request), p_district(request)
    spec = INDICATORS[ind]
    join, where, params = district_filter(district_id, 'v')
    base = f'FROM validation_2026 v {join} WHERE v.indicator = %s AND v.actual IS NOT NULL {where}'
    monthly = rows(f'SELECT v.obs_month, avg(v.actual) AS actual, avg(v.forecast) AS forecast, '
                   f'avg(v.climatology) AS climatology, count(*) AS n, '
                   f'sqrt(avg((v.forecast - v.actual) ^ 2)) AS rmse_model, '
                   f'sqrt(avg((v.climatology - v.actual) ^ 2)) AS rmse_clim {base} '
                   f'GROUP BY v.obs_month ORDER BY v.obs_month', [ind] + params)
    m = rows(f"""
        WITH x AS (SELECT v.actual, v.forecast, v.climatology {base}),
             mean AS (SELECT avg(actual) AS a FROM x)
        SELECT count(*) AS n,
               sqrt(avg((forecast - actual) ^ 2)) AS rmse_model, avg(abs(forecast - actual)) AS mae_model,
               sqrt(avg((climatology - actual) ^ 2)) AS rmse_clim, avg(abs(climatology - actual)) AS mae_clim,
               1 - sum((forecast - actual) ^ 2) / nullif(sum((actual - mean.a) ^ 2), 0) AS r2_model,
               1 - sum((climatology - actual) ^ 2) / nullif(sum((actual - mean.a) ^ 2), 0) AS r2_clim
        FROM x, mean GROUP BY mean.a""", [ind] + params)
    metrics = m[0] if m else {}
    if metrics.get('rmse_model') and metrics.get('rmse_clim'):
        metrics['vs_climatology_pct'] = (metrics['rmse_model'] / metrics['rmse_clim'] - 1) * 100
    dec = spec['decimals'] + 2
    return JsonResponse({
        'indicator': ind, 'name': spec['name'], 'unit': spec['unit'], 'decimals': spec['decimals'],
        'district_id': district_id,
        'months': [ym(r['obs_month']) for r in monthly],
        'actual': [rnd(r['actual'], dec) for r in monthly],
        'forecast': [rnd(r['forecast'], dec) for r in monthly],
        'climatology': [rnd(r['climatology'], dec) for r in monthly],
        'n': [r['n'] for r in monthly],
        'rmse_model': [rnd(r['rmse_model'], dec) for r in monthly],
        'rmse_clim': [rnd(r['rmse_clim'], dec) for r in monthly],
        'metrics': {k: (rnd(v, 6) if k != 'n' else v) for k, v in metrics.items()},
        'note': 'Dự báo trước 1 tháng. Chỉ số Landsat chỉ tính trên ô-tháng quan sát thật. '
                'RMSE, MAE, R² tính ở mức ô-tháng.',
    })


@api
def ranking(request):
    mode, ind = p_mode(request), p_indicator(request)
    spec = INDICATORS[ind]
    month = p_month(request, history_months() if mode == 'history' else forecast_months())
    view = p_view(request) if mode == 'forecast' else None
    observed_only = p_flag(request, 'observed_only')
    data = month_values(mode, ind, month, view, observed_only)

    cell_district = cache.get_or_set('cell_district', lambda: {
        r['cell_id']: r['district_id'] for r in rows('SELECT cell_id, district_id FROM grid_cell')}, CACHE_SECONDS)
    acc = {}
    for c, v, k in data:
        a = acc.setdefault(cell_district[c], {'sum': 0.0, 'n': 0, 'strong': 0, 'n_class': 0})
        a['sum'] += v
        a['n'] += 1
        if k is not None:
            a['n_class'] += 1
            a['strong'] += k >= STRONG_UTFVI_CLASS

    out = []
    for d in districts():
        a = acc.get(d['district_id'])
        out.append({
            'district_id': d['district_id'], 'name': d['name_vi'], 'n_cells': d['n_cells'],
            'n_values': a['n'] if a else 0,
            'mean': rnd(a['sum'] / a['n'], spec['decimals'] + 2) if a else None,
            'strong_share': (a['strong'] / a['n_class'] if a and a['n_class'] else None) if ind == 'UTFVI' else None,
            'small': d['n_cells'] < SMALL_DISTRICT_CELLS,
        })
    out.sort(key=lambda r: (r['mean'] is None, -(r['mean'] or 0)))
    return JsonResponse({'mode': mode, 'indicator': ind, 'month': ym(month), 'view': view,
                         'name': spec['name'], 'unit': spec['unit'], 'decimals': spec['decimals'],
                         'districts': out})


@api
def locate(request):
    try:
        lon, lat = float(request.GET['lon']), float(request.GET['lat'])
    except (KeyError, ValueError):
        raise ParamError('lon và lat phải là số')
    r = rows('SELECT c.cell_id, d.district_id, d.name_vi FROM grid_cell c JOIN district d USING (district_id) '
             'WHERE ST_Contains(c.geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) LIMIT 1', [lon, lat])
    if not r:
        return JsonResponse({'found': False})
    return JsonResponse({'found': True, 'cell_id': r[0]['cell_id'], 'district_id': r[0]['district_id'],
                         'district': r[0]['name_vi']})
