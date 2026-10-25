# check_api.py - gọi tất cả API trên database thật và kiểm tra kết quả.
# Cách dùng: python manage.py check_api
# (Không dùng "manage.py test" vì trình chạy test tạo database rỗng, còn các bảng ở đây là managed=False.)
import json

from django.core.management.base import BaseCommand
from django.test import Client


class Command(BaseCommand):
    help = 'Gọi tất cả endpoint của WebGIS trên database thật và báo lỗi nếu có'

    def handle(self, *args, **opts):
        c = Client(HTTP_HOST='localhost')
        self.failures = 0

        def get(url, status=200):
            r = c.get(url)
            ok = r.status_code == status
            self.report(ok, f'{url} -> {r.status_code}')
            return json.loads(r.content) if r['Content-Type'].startswith('application') else None

        h = get('/api/health/')
        # 7 chỉ số gốc + T2M, PRECIP (Cell 22b): forecast +15.848, validation +31.696, reliability +8
        expected = {'district': 22, 'grid_cell': 1981, 'observation': 158480, 'forecast': 71316,
                    'validation_2026': 140680, 'reliability': 36, 'district_month': 1760}
        self.report(h['rows'] == expected, f'số dòng các bảng: {h["rows"]}')

        m = get('/api/meta/')
        self.report(len(m['history_months']) == 80 and m['history_months'][-1] == '2026-08', 'meta: 80 tháng lịch sử')
        self.report([f['month'] for f in m['forecast_months']] == ['2026-09', '2026-10', '2026-11', '2026-12'],
                    'meta: 4 tháng dự báo')
        self.report(len(m['districts']) == 22, 'meta: 22 quận/huyện')

        cells = get('/api/cells/')
        self.report(len(cells['features']) == 1981, 'cells: 1.981 ô GeoJSON')
        dists = get('/api/districts/')
        self.report(len(dists['features']) == 22, 'districts: 22 đa giác')

        page = c.get('/')
        self.report(page.status_code == 200 and b'id="map"' in page.content, 'trang chủ hiển thị')

        did = m['districts'][0]['id']
        for ind in [i['id'] for i in m['indicators']]:
            v = get(f'/api/values/?mode=history&indicator={ind}&month=2026-08')
            self.report(v['n_cells'] > 1800, f'values {ind} 2026-08: {v["n_cells"]} ô, thang {v["range"]}')
            for view in ('forecast', 'climatology', 'diff'):
                v = get(f'/api/values/?mode=forecast&indicator={ind}&month=2026-09&view={view}')
                self.report(v['n_cells'] == 1981, f'values dự báo {ind} {view}: {v["n_cells"]} ô')
            s = get(f'/api/series/?indicator={ind}&district={did}')
            self.report(len(s['city']) == 80 and len(s['district']) == 80, f'series {ind}')
            f = get(f'/api/forecast/?indicator={ind}&district=all')
            self.report(len(f['forecast']) == 4 and len(f['reliability']) == 4, f'forecast {ind}')
            val = get(f'/api/validation/?indicator={ind}&district=all')
            # RMSE mức ô của toàn thành phố phải trùng bảng reliability (horizon 1)
            rel = f['reliability'][0]
            same = abs(val['metrics']['rmse_model'] - rel['rmse_model']) < 1e-3 * max(1, rel['rmse_model'])
            self.report(same, f'validation {ind}: RMSE {val["metrics"]["rmse_model"]:.5f} '
                              f'(reliability {rel["rmse_model"]:.5f}), so khí hậu '
                              f'{val["metrics"]["vs_climatology_pct"]:+.1f}%')
            r = get(f'/api/ranking/?mode=history&indicator={ind}&month=2026-08&observed_only=1')
            self.report(len(r['districts']) == 22, f'ranking {ind}')

        bad = get('/api/values/?mode=history&indicator=LST&month=2020-05&observed_only=1')
        self.report(bad['n_cells'] == 0 and bad['landsat_missing'], 'tháng thiếu Landsat: không có ô quan sát')
        loc = get('/api/locate/?lon=106.70&lat=10.78')
        self.report(loc['found'], f'locate (106.70, 10.78): {loc.get("district")}')

        # Tham số sai phải trả 400
        for url in ['/api/values/?mode=history&indicator=XYZ&month=2026-08',
                    '/api/values/?mode=history&indicator=LST&month=2030-01',
                    '/api/values/?mode=history&indicator=LST&month=abc',
                    "/api/values/?mode=history&indicator=LST;DROP TABLE x&month=2026-08",
                    '/api/series/?indicator=LST&district=999',
                    '/api/values/?mode=forecast&indicator=LST&month=2026-09&view=x',
                    '/api/locate/?lon=a&lat=b']:
            get(url, status=400)

        if self.failures:
            self.stdout.write(self.style.ERROR(f'\n{self.failures} kiểm tra KHÔNG đạt'))
        else:
            self.stdout.write(self.style.SUCCESS('\nTất cả kiểm tra đều đạt'))

    def report(self, ok, msg):
        if not ok:
            self.failures += 1
        self.stdout.write((self.style.SUCCESS('  ĐẠT ') if ok else self.style.ERROR('  LỖI ')) + msg)
