# ===== CELL 22b: DỰ BÁO NHIỆT ĐỘ KHÔNG KHÍ (T2M) VÀ LƯỢNG MƯA (PRECIP) =====
# Cùng quy trình với Cell 22 (dự báo phần lệch so với khí hậu, XGBoost, dự báo trước 1-4 tháng),
# thêm đánh giá 4 giai đoạn như Cell 17. Không ghi đè file kết quả cũ của 7 chỉ số.
import sys, os, time, importlib, json, zipfile
import numpy as np, pandas as pd
BASE = '/content/drive/MyDrive/DACN_HCM_Environment'
sys.path.insert(0, BASE)
import pipeline as pl; importlib.reload(pl)
try:
    display
except NameError:
    display = print

H = [1, 2, 3, 4]
TARGETS = ['T2M', 'PRECIP']
UNITS = {'T2M': '°C', 'PRECIP': 'mm/tháng'}
CLIP = {'PRECIP': (0, None)}                               # lượng mưa không âm

D0 = pl.load(BASE)
FOLDS = pl.make_folds(D0)
_, f4_end, f4_idx = FOLDS[3]                               # kiểm thử 2026 (T1-T8)
D1 = pl.extend(D0, max(H))
T0, N = D0.T, D0.N
info = D0.d.drop_duplicates('cell_id').set_index('cell_id')[['lon', 'lat', 'district']].loc[D0.cells]
print(f'Dữ liệu đến {D0.dates[-1]:%Y-%m}; sẽ dự báo {D1.dates[T0]:%Y-%m} đến {D1.dates[T0 + max(H) - 1]:%Y-%m}')

# ERA5-Land có ô gốc khoảng 9 km nên nhiều ô lưới 1 km dùng chung một giá trị: ghi lại để viết hạn chế
for tgt in TARGETS:
    A = D0.RAW[tgt]
    n_uniq = np.median([len(np.unique(np.round(A[t][np.isfinite(A[t])], 4))) for t in range(T0)])
    print(f'{tgt}: trung vị số giá trị khác nhau trong 1 tháng = {n_uniq:.0f} / {N} ô; '
          f'độ lệch chuẩn giữa các ô (trung vị) = {np.nanmedian(np.nanstd(A, axis=1)):.3f} {UNITS[tgt]}')

PARTS = f'{BASE}/outputs/parts'
os.makedirs(PARTS, exist_ok=True)
t0 = time.time()
for tgt in TARGETS:
    paths = {k: f'{PARTS}/{k}_{tgt}.csv' for k in ['skill', 'fc', 'test', 'folds']}
    if all(os.path.exists(p) for p in paths.values()):
        print(f'{tgt}: đã có kết quả, bỏ qua'); continue

    # (A) Đánh giá 4 giai đoạn, dự báo trước 1 tháng (giống Cell 17)
    folds = []
    for name, end, idx in FOLDS:
        fd = pl.fold_data(D0, tgt, end, idx, 1)
        mdl, best = pl.fit_xgb(fd)
        pred = mdl.predict(fd.Xte) + fd.clte
        good = np.isfinite(fd.yte) & np.isfinite(pred) & np.isfinite(fd.clte)
        rm = float(np.sqrt(np.mean((pred[good] - fd.yte[good]) ** 2)))
        rc = float(np.sqrt(np.mean((fd.clte[good] - fd.yte[good]) ** 2)))
        wins = 0
        for t in idx:                                       # số tháng mô hình thắng khí hậu
            k = good & (fd.tte == t)
            if k.any():
                wins += np.mean((pred[k] - fd.yte[k]) ** 2) < np.mean((fd.clte[k] - fd.yte[k]) ** 2)
        folds.append({'chỉ số': tgt, 'giai đoạn': name, 'RMSE mô hình': rm, 'RMSE khí hậu': rc,
                      'so khí hậu (%)': (rm / rc - 1) * 100, 'số tháng thắng khí hậu': int(wins),
                      'số tháng': len(idx), 'số cây': best})

    # (B) Kiểm thử 2026 theo khoảng cách dự báo + dự báo 9-12/2026 (giống Cell 22)
    skill, fc, tst = [], [], []
    for h in H:
        fd = pl.fold_data(D0, tgt, f4_end, f4_idx, h)
        mdl, best = pl.fit_xgb(fd)
        pred = mdl.predict(fd.Xte) + fd.clte
        good = np.isfinite(fd.yte) & np.isfinite(pred) & np.isfinite(fd.clte)
        y, p, c = fd.yte[good], pred[good], fd.clte[good]
        res = y - p
        q10, q90 = np.quantile(res, 0.1), np.quantile(res, 0.9)
        rm, rc = float(np.sqrt(np.mean(res ** 2))), float(np.sqrt(np.mean((y - c) ** 2)))
        skill.append({'chỉ số': tgt, 'dự báo trước (tháng)': h, 'số dòng kiểm thử': int(good.sum()),
                      'RMSE mô hình': rm, 'RMSE khí hậu': rc, 'so khí hậu (%)': (rm / rc - 1) * 100,
                      'sai số q10': q10, 'sai số q90': q90, 'số cây': best})
        if h == 1:
            cidx = np.tile(np.arange(N), len(f4_idx))[good]
            tst.append(pd.DataFrame({'cell_id': D0.cells[cidx], 'date': D0.dates[fd.tte[good]], 'chỉ số': tgt,
                                     'thực tế': y, 'dự báo': p, 'khí hậu': c}))
        t_target = T0 - 1 + h
        fd2 = pl.fold_data(D1, tgt, T0 - 1, [t_target], h)
        mdl2, _ = pl.fit_xgb(fd2)
        p2 = mdl2.predict(fd2.Xte) + fd2.clte
        lo, hi = p2 + q10, p2 + q90
        if tgt in CLIP:
            a, b = CLIP[tgt]; p2, lo, hi = np.clip(p2, a, b), np.clip(lo, a, b), np.clip(hi, a, b)
        fc.append(pd.DataFrame({'cell_id': D0.cells, 'lon': info.lon.values, 'lat': info.lat.values,
                                'district': info.district.values, 'chỉ số': tgt, 'date': D1.dates[t_target],
                                'dự báo trước (tháng)': h, 'dự báo': p2, 'cận dưới': lo, 'cận trên': hi,
                                'khí hậu': fd2.clte}))
    pd.DataFrame(folds).to_csv(paths['folds'], index=False, encoding='utf-8-sig')
    pd.DataFrame(skill).to_csv(paths['skill'], index=False, encoding='utf-8-sig')
    pd.concat(fc).to_csv(paths['fc'], index=False, encoding='utf-8-sig')
    pd.concat(tst).to_csv(paths['test'], index=False, encoding='utf-8-sig')
    print(f'{tgt}: xong (tổng {time.time() - t0:.0f} giây)')

# ---------- Gộp kết quả (file riêng, không ghi đè kết quả 7 chỉ số cũ) ----------
read = lambda k: pd.concat([pd.read_csv(f'{PARTS}/{k}_{t}.csv') for t in TARGETS], ignore_index=True)
FO, S, FC, TS = read('folds'), read('skill'), read('fc'), read('test')
OUT = f'{BASE}/outputs'
FO.to_csv(f'{OUT}/weather_backtest_by_fold.csv', index=False, encoding='utf-8-sig')
S.to_csv(f'{OUT}/weather_skill_by_horizon.csv', index=False, encoding='utf-8-sig')
FC.to_csv(f'{OUT}/weather_forecast_2026_09_12.csv', index=False, encoding='utf-8-sig')
TS.to_csv(f'{OUT}/weather_test_2026_h1.csv', index=False, encoding='utf-8-sig')

# ---------- Gói dữ liệu cho web (Django/PostgreSQL) ----------
W = f'{OUT}/dashboard_weather'
os.makedirs(W, exist_ok=True)
hist = D0.d[['cell_id', 'date'] + TARGETS].copy()
hist['date'] = pd.to_datetime(hist.date).dt.strftime('%Y-%m-%d')
hist.to_csv(f'{W}/weather_history.csv.gz', index=False, encoding='utf-8-sig')
FC.rename(columns={'chỉ số': 'indicator', 'dự báo trước (tháng)': 'horizon', 'dự báo': 'forecast',
                   'cận dưới': 'lower', 'cận trên': 'upper', 'khí hậu': 'climatology'})[
    ['cell_id', 'indicator', 'date', 'horizon', 'forecast', 'lower', 'upper', 'climatology']
].to_csv(f'{W}/weather_forecast.csv.gz', index=False, encoding='utf-8-sig')
TS.rename(columns={'chỉ số': 'indicator', 'thực tế': 'actual', 'dự báo': 'forecast', 'khí hậu': 'climatology'})[
    ['cell_id', 'date', 'indicator', 'actual', 'forecast', 'climatology']
].to_csv(f'{W}/weather_test_2026.csv.gz', index=False, encoding='utf-8-sig')
S.rename(columns={'chỉ số': 'indicator', 'dự báo trước (tháng)': 'horizon', 'RMSE mô hình': 'rmse_model',
                  'RMSE khí hậu': 'rmse_climatology', 'so khí hậu (%)': 'vs_climatology_pct',
                  'sai số q10': 'err_q10', 'sai số q90': 'err_q90'})[
    ['indicator', 'horizon', 'rmse_model', 'rmse_climatology', 'vs_climatology_pct', 'err_q10', 'err_q90']
].to_csv(f'{W}/weather_reliability.csv', index=False, encoding='utf-8-sig')
FO.to_csv(f'{W}/weather_backtest_by_fold.csv', index=False, encoding='utf-8-sig')
json.dump({'units': UNITS}, open(f'{W}/weather_meta.json', 'w', encoding='utf-8'), ensure_ascii=False)
with zipfile.ZipFile(f'{OUT}/dashboard_weather.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(W)):
        z.write(f'{W}/{f}', f)
print(f'\nĐã tạo {OUT}/dashboard_weather.zip ({os.path.getsize(f"{OUT}/dashboard_weather.zip") / 1e6:.1f} MB)')

# ---------- Kết quả ----------
print('\n=== ĐÁNH GIÁ 4 GIAI ĐOẠN, DỰ BÁO TRƯỚC 1 THÁNG (% so với khí hậu, âm = tốt hơn) ===')
display(FO.pivot(index='chỉ số', columns='giai đoạn', values='so khí hậu (%)').round(1))
print('Số tháng mô hình thắng khí hậu:')
display(FO.groupby('chỉ số')[['số tháng thắng khí hậu', 'số tháng']].sum())
print('RMSE khí hậu theo giai đoạn:')
display(FO.pivot(index='chỉ số', columns='giai đoạn', values='RMSE khí hậu').round(3))
print('\n=== KIỂM THỬ 2026 THEO KHOẢNG CÁCH DỰ BÁO (% so với khí hậu) ===')
display(S.pivot(index='chỉ số', columns='dự báo trước (tháng)', values='so khí hậu (%)').round(1))
display(S.pivot(index='chỉ số', columns='dự báo trước (tháng)', values='RMSE mô hình').round(3))
print('\nTrung bình toàn thành phố của dự báo 9-12/2026 (mô hình so với khí hậu):')
display(FC.groupby(['chỉ số', 'date'])[['dự báo', 'khí hậu', 'cận dưới', 'cận trên']].mean().round(2))
