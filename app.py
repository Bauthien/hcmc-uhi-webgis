# app.py - Dashboard môi trường TP.HCM 2020-2026 (Streamlit + Folium)
# Chạy:  streamlit run app.py     (đặt thư mục dashboard_data cạnh file này)
import os, json, html
import numpy as np
import pandas as pd
import streamlit as st
import folium
import altair as alt
from branca.element import MacroElement, Template
from branca.colormap import linear, LinearColormap
from streamlit_folium import st_folium

st.set_page_config(page_title='Môi trường TP.HCM 2020-2026', layout='wide')

st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
:root {
    --bg: #07111f; --panel: #0b1929; --panel-2: #0f2033; --line: #1b3047;
    --text: #e7f1fb; --muted: #8298b1; --cyan: #16c8f4; --cyan-deep: #078ab7; --primary-color: #16c8f4;
    --green: #31d79a; --radius: 16px;
}
html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }
.stApp { background: radial-gradient(ellipse at 72% -20%, #10253b 0, transparent 42%), var(--bg); color: var(--text); }
[data-testid="stHeader"] { background: rgba(7,17,31,.92); border-bottom: 1px solid var(--line); }
[data-testid="stToolbar"] { right: 1rem; }
[data-testid="stSidebar"] { background: #081422; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] > div:first-child { padding-top: 1.15rem; }
[data-testid="stSidebar"] h1 { font-size: 1.22rem; color: var(--text); letter-spacing: -.03em; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #a8b8ca; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { font-size: .84rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .42rem .55rem; border-radius: 9px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: #10243a; }
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] { background: #0b2032; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child { background: transparent !important; border: 1px solid #48627b !important; }
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child { background: var(--cyan) !important; border-color: var(--cyan) !important; }
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child > div { background: #07111f !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div { background: var(--panel-2); border-color: var(--line); border-radius: 10px; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] span { color: #dceaf7 !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] { background: var(--panel-2) !important; border: 1px solid var(--line) !important; border-radius: 10px; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"]:focus-within { border-color: var(--cyan) !important; box-shadow: 0 0 0 1px #16c8f455; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] input[role="combobox"] { color: #dceaf7 !important; caret-color: var(--cyan); }
[data-testid="stSidebar"] [data-testid="stSelectbox"] button { color: #8298b1 !important; }
[role="listbox"] { background: #0f2033 !important; border: 1px solid var(--line) !important; }
[role="option"] { color: #dceaf7 !important; }
[data-testid="stSidebar"] [data-testid="stSlider"] [data-rac][style*="position: absolute"] { background: var(--cyan) !important; box-shadow: 0 0 14px #16c8f477; }
[data-testid="stSidebar"] [data-testid="stSlider"] [data-rac][style*="position: relative"] > div:first-child { background: #20364c !important; }
.block-container { max-width: 1540px; padding-top: 1.25rem; padding-bottom: 3rem; }
h1, h2, h3 { color: var(--text) !important; letter-spacing: -.035em; }
h2 { font-size: 1.25rem !important; font-weight: 700 !important; }
h3 { font-size: 1.02rem !important; font-weight: 650 !important; }
p, li { color: #a6b7ca; }
[data-testid="stTabs"] [role="tablist"] { gap: .45rem; border-bottom: 1px solid var(--line); }
[data-testid="stTab"] { color: #91a4ba; padding: .72rem .9rem; font-weight: 600; border-radius: 10px 10px 0 0; }
[data-testid="stTab"][aria-selected="true"] { color: #04131f !important; background: var(--cyan); }
[data-testid="stTab"][aria-selected="true"] p { color: #04131f !important; }
.react-aria-SelectionIndicator { background: var(--cyan) !important; height: 3px !important; }
[data-testid="stRadio"] input, [data-testid="stCheckbox"] input { accent-color: var(--cyan); }
[data-testid="stMetric"] { background: linear-gradient(145deg, #10243a, #0b1929); border: 1px solid var(--line); border-top: 2px solid #0c6284; border-radius: var(--radius); padding: 1.05rem 1.15rem; min-height: 132px; }
[data-testid="stMetricLabel"] { color: #91a6bc !important; font-size: .79rem; font-weight: 600; }
[data-testid="stMetricValue"] { color: #e6f7ff !important; font-weight: 750; letter-spacing: -.04em; }
[data-testid="stMetricDelta"] { font-size: .75rem; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
[data-testid="stDataFrame"] [role="grid"] { background: #0b1929; }
[data-testid="stAlert"] { border: 1px solid #1b4058; border-radius: 12px; background: #0c1d30; }
[data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 12px; background: #0b1929; }
[data-testid="stExpander"] details > summary { background: #0d1b2c !important; color: #a6bdd3 !important; border-radius: 11px; }
[data-testid="stExpander"] details > summary:hover { background: #10243a !important; color: var(--cyan) !important; }
[data-testid="stExpander"] details > summary p { color: inherit !important; }
[data-testid="stExpander"] details > summary [data-testid="stIconMaterial"] { color: var(--cyan) !important; }
[data-testid="stExpander"] [data-testid="stExpanderDetails"] { background: #0b1929; border-top: 1px solid var(--line); }
[data-testid="stDownloadButton"] button, .stButton button { border-radius: 10px; border: 1px solid #28445e; background: #102238; color: #dceaf7; font-weight: 600; }
[data-testid="stDownloadButton"] button:hover, .stButton button:hover { border-color: var(--cyan); color: var(--cyan); }
div[data-testid="stMarkdownContainer"] hr { border-color: var(--line); }
.page-hero { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin:.4rem 0 1.25rem; }
.hero-kicker { color: var(--cyan); font-size:.69rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; margin-bottom:.55rem; }
.hero-title { color:var(--text); font-size:clamp(1.75rem,3vw,2.55rem); line-height:1.12; font-weight:750; letter-spacing:-.055em; }
.hero-title span { color:var(--cyan); }
.hero-subtitle { color:#8fa4ba; font-size:.84rem; margin-top:.55rem; }
.brand-status { color:#8298b1; font-size:.68rem; letter-spacing:.09em; font-weight:700; white-space:nowrap; padding-bottom:.35rem; }
.brand-status i { display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--green); margin-right:.45rem; box-shadow:0 0 12px #31d79a99; }
.insight-banner { display:flex; align-items:flex-start; gap:.9rem; padding:1rem 1.15rem; margin:.35rem 0 1.25rem; border:1px solid #154563; border-left:4px solid var(--cyan); border-radius:13px; background:linear-gradient(100deg,#0c2338,#0a1928); box-shadow:0 6px 20px #02091444; }
.insight-icon { width:34px; height:34px; display:grid; place-items:center; flex:none; border-radius:10px; background:#073047; color:var(--cyan); font-weight:800; margin-top:.15rem; }
.insight-header { display:flex; flex-wrap:wrap; align-items:center; gap:.5rem; margin-bottom:.45rem; }
.insight-copy strong { color:#e8f4fc; font-size:.88rem; display:block; margin-bottom:.2rem; }
.insight-copy p { margin:.2rem 0 0; color:#95abbf; font-size:.76rem; line-height:1.65; }
.panel-heading { display:flex; align-items:center; justify-content:space-between; margin:.35rem 0 .65rem; }
.panel-heading span { color:var(--muted); font-size:.73rem; }
.section-title { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin:1.25rem 0 .7rem; }
.section-title h2 { margin:0; color:var(--text); font-size:1.05rem !important; }
.section-title p { margin:.25rem 0 0; color:var(--muted); font-size:.73rem; }
.table-shell { width:100%; overflow-x:auto; border:1px solid var(--line); border-radius:13px; background:#0b1929; box-shadow:0 8px 24px #02091424; }
.dark-table { width:100%; min-width:620px; border-collapse:collapse; color:#dceaf7; font-size:.78rem; }
.dark-table thead { background:#0d1b2c; }
.dark-table th { color:#8298b1; font-size:.65rem; font-weight:700; letter-spacing:.075em; text-align:left; text-transform:uppercase; padding:.78rem .95rem; border-bottom:1px solid var(--line); white-space:nowrap; }
.dark-table td { padding:.8rem .95rem; border-bottom:1px solid #1a2b3e; white-space:nowrap; }
.dark-table tbody tr:last-child td { border-bottom:0; }
.dark-table tbody tr:hover { background:#10243a; }
.dark-table tbody tr.is-selected { background:#103047; box-shadow:inset 3px 0 #16c8f4; }
.dark-table .num { color:var(--cyan); font-weight:700; font-variant-numeric:tabular-nums; }
.rank-number { display:inline-flex; min-width:28px; height:24px; align-items:center; justify-content:center; border:1px solid #29445e; border-radius:6px; color:#9bb1c8; font-size:.68rem; }
.rank-number.is-top { border-color:#087a9d; background:#073047; color:var(--cyan); }
.status-pill { display:inline-flex; align-items:center; gap:.38rem; padding:.23rem .55rem; border-radius:6px; font-size:.66rem; font-weight:700; }
.status-pill::before { content:''; width:6px; height:6px; border-radius:50%; background:currentColor; }
.status-high { color:#ff7393; background:#64223b55; }
.status-mid { color:#ffb648; background:#70481955; }
.status-low { color:#42d9a4; background:#124a3a55; }
.status-cyan { color:#16c8f4; background:#07304777; border: 1px solid #14496b; }
.status-neutral { color:#9bb2c8; background:#16263877; border: 1px solid #23394e; }
.hero-tag-list { display:flex; flex-wrap:wrap; align-items:center; gap:.5rem; margin-top:.6rem; }
.hero-tag { display:inline-flex; align-items:center; gap:.35rem; padding:.24rem .65rem; border-radius:7px; font-size:.7rem; font-weight:600; border:1px solid #1e3a54; background:#0c1c2e; color:#bed2e4; }
.hero-tag strong { color:#f1f8ff; font-weight:700; }
.info-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.8rem; margin:.8rem 0 1.2rem; }
.info-card { min-height:118px; padding:1rem 1.05rem; border:1px solid var(--line); border-top:2px solid #0d5775; border-radius:13px; background:linear-gradient(145deg,#10243a,#0b1929); }
.info-card .eyebrow { color:var(--cyan); font-size:.65rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
.info-card strong { display:block; margin:.42rem 0 .25rem; color:#e7f1fb; font-size:.88rem; }
.info-card p { margin:0; color:#8fa4ba; font-size:.74rem; line-height:1.65; }
.callout { margin:.85rem 0; padding:.85rem 1rem; border:1px solid #1b4058; border-left:3px solid var(--cyan); border-radius:10px; background:#0c1d30; color:#a8bfd3; font-size:.78rem; line-height:1.7; }
.callout.warning { border-color:#66502a; border-left-color:#ffb648; background:#241e15; }
.callout strong { color:#e5f1fb; }
.note-list { display:grid; gap:.55rem; margin:.7rem 0; }
.note-item { display:flex; gap:.65rem; padding:.7rem .85rem; border:1px solid var(--line); border-radius:10px; background:#0b1929; color:#a6b7ca; font-size:.76rem; line-height:1.6; }
.note-item::before { content:'!'; display:grid; place-items:center; flex:none; width:19px; height:19px; border-radius:50%; background:#17354a; color:var(--cyan); font-size:.68rem; font-weight:800; }
@media (max-width:760px) { .info-grid { grid-template-columns:1fr; } .section-title { align-items:flex-start; flex-direction:column; } }
@media (max-width: 760px) { .block-container { padding:1rem .8rem 2rem; } .page-hero { align-items:flex-start; flex-direction:column; } [data-testid="stTab"] { padding:.55rem .55rem; font-size:.76rem; } }
</style>
''', unsafe_allow_html=True)

DATA = os.environ.get('DASHBOARD_DATA', 'dashboard_data')
ALL = 'Toàn thành phố'

IND = {
    'UTFVI': ('Chỉ số sinh thái nhiệt (UTFVI)', ''),
    'LST': ('Nhiệt độ bề mặt (LST)', '°C'),
    'NDVI': ('Chỉ số thực vật (NDVI)', ''),
    'TVDI': ('Chỉ số hạn khô (TVDI)', ''),
    'NO2': ('NO₂ tầng đối lưu', 'µmol/m²'),
    'CO': ('CO', 'mmol/m²'),
    'AOD': ('Độ dày sol khí (AOD)', ''),
}
CMAPS = {'UTFVI': linear.YlOrRd_09, 'LST': linear.YlOrRd_09, 'NDVI': linear.YlGn_09, 'TVDI': linear.YlOrBr_09,
         'NO2': linear.PuRd_09, 'CO': linear.PuRd_09, 'AOD': linear.BuPu_09}
LEVEL_SEMANTICS = {
    'LST': ('Mát mẻ', 'Nóng gắt'),
    'NDVI': ('Thảm xanh thưa', 'Xanh tươi dồi dào'),
    'TVDI': ('Ẩm ướt dồi dào', 'Khô hạn nghiêm trọng'),
    'NO2': ('Trong lành', 'Khí thải ô nhiễm cao'),
    'CO': ('Mật độ thấp', 'Nồng độ cao'),
    'AOD': ('Bầu trời quang đãng', 'Mù sol khí dày'),
    'UTFVI': ('Sinh thái tốt', 'Đảo nhiệt gay gắt'),
}
LANDSAT = {'LST', 'NDVI', 'TVDI', 'UTFVI'}
CLASS_COLORS = ['#1a9850', '#a6d96a', '#fee08b', '#fdae61', '#f46d43', '#a50026']


@st.cache_data
def load():
    hist = pd.read_csv(f'{DATA}/history.csv.gz', parse_dates=['date'])
    fc = pd.read_csv(f'{DATA}/forecast.csv.gz', parse_dates=['date'])
    ts = pd.read_csv(f'{DATA}/test_2026.csv.gz', parse_dates=['date'])
    rel = pd.read_csv(f'{DATA}/reliability.csv')
    cells = pd.read_csv(f'{DATA}/cells.csv')
    meta = json.load(open(f'{DATA}/meta.json', encoding='utf-8'))
    return hist, fc, ts, rel, cells, meta


if not os.path.exists(f'{DATA}/history.csv.gz'):
    st.error(f'Không tìm thấy dữ liệu trong thư mục "{DATA}". Giải nén dashboard_data.zip vào thư mục này.')
    st.stop()

hist, fc, ts, rel, cells, meta = load()
CLASS_NAMES = meta['utfvi_class_names']
BAD = set(meta['months_without_landsat'])
districts = sorted(cells.district_vi.unique())


def classify_utfvi(values):
    """Phân cấp UTFVI thành 6 mức dựa trên ngưỡng: <=0 (1), (0, 0.005] (2), ..., >0.02 (6)."""
    thresholds = np.asarray(meta['utfvi_thresholds'], dtype=float)
    return np.clip(np.digitize(np.asarray(values, dtype=float), bins=thresholds, right=True) + 1, 1, 6)


def reliability_summary(rmse_model, rmse_climatology):
    """Đánh giá kỹ năng mô hình so với khí hậu; tỉ lệ âm nghĩa là sai số mô hình thấp hơn."""
    if pd.isna(rmse_model) or pd.isna(rmse_climatology) or rmse_climatology <= 0:
        return np.nan, 'Chưa đủ dữ liệu'
    delta_pct = (rmse_model / rmse_climatology - 1) * 100
    if delta_pct <= -5:
        label = 'Cải thiện so với khí hậu'
    elif delta_pct < 0:
        label = 'Cải thiện nhẹ'
    elif delta_pct <= 5:
        label = 'Tương đương khí hậu'
    else:
        label = 'Kém hơn khí hậu'
    return delta_pct, label


def display_precision(indicator):
    if indicator in {'LST', 'NO2', 'CO'}:
        return 1
    elif indicator == 'UTFVI':
        return 4
    return 3


def display_unit(indicator):
    unit_text = IND[indicator][1]
    return unit_text if unit_text else 'Không thứ nguyên'


def rank_status_styles(indicator):
    levels = ['Rất cao', 'Cao', 'Trung bình', 'Thấp']
    if indicator == 'NDVI':
        return {levels[0]: 'status-low', levels[1]: 'status-low',
                levels[2]: 'status-mid', levels[3]: 'status-high'}
    return {levels[0]: 'status-high', levels[1]: 'status-high',
            levels[2]: 'status-mid', levels[3]: 'status-low'}


def evaluate_indicator_status(indicator, val):
    """Đánh giá phân loại trạng thái môi trường và trả về (css_class, nhãn, mô tả chi tiết)."""
    if pd.isna(val):
        return 'status-mid', 'Chưa có dữ liệu', 'Chưa đủ dữ liệu quan trắc cho thời điểm này.'
    val = float(val)
    if indicator == 'UTFVI':
        cls = int(classify_utfvi([val])[0])
        cls_name = CLASS_NAMES[cls - 1]
        if cls <= 2:
            return 'status-low', f'Sinh thái tốt ({cls_name})', f'Áp lực sinh thái nhiệt ở mức {cls_name.lower()}, vi khí hậu mát mẻ và thảm xanh hấp thụ nhiệt hiệu quả.'
        elif cls == 3:
            return 'status-mid', f'Sinh thái trung bình ({cls_name})', f'Áp lực sinh thái nhiệt ở mức {cls_name.lower()}, xuất hiện đảo nhiệt cục bộ tại các cụm dân cư mật độ cao.'
        elif cls <= 5:
            return 'status-high', f'Cảnh báo nhiệt ({cls_name})', f'Áp lực đảo nhiệt đô thị ở mức {cls_name.lower()}, nguy cơ tích tụ nhiệt bề mặt ảnh hưởng tiện nghi nhiệt.'
        else:
            return 'status-high', f'Báo động nhiệt ({cls_name})', f'Áp lực đảo nhiệt ở mức {cls_name.lower()} (cực kỳ nghiêm trọng), nguy cơ stress nhiệt diện rộng.'
    elif indicator == 'LST':
        if val < 30.0:
            return 'status-low', f'Nhiệt độ mát mẻ ({val:.1f}°C)', f'Nhiệt độ bề mặt trung bình đạt {val:.1f}°C, không khí dễ chịu và ít tích tụ nhiệt bề mặt.'
        elif val <= 35.0:
            return 'status-low', f'Nhiệt độ bình thường ({val:.1f}°C)', f'Nhiệt độ bề mặt trung bình đạt {val:.1f}°C, ở mức vi khí hậu điển hình theo mùa của TP.HCM.'
        elif val <= 38.0:
            return 'status-mid', f'Nhiệt độ khá cao ({val:.1f}°C)', f'Nhiệt độ bề mặt trung bình đạt {val:.1f}°C, hấp thụ nhiệt bề mặt tăng cao trong mùa khô hoặc trưa nắng.'
        else:
            return 'status-high', f'Nhiệt độ rất cao ({val:.1f}°C)', f'Nhiệt độ bề mặt trung bình đạt {val:.1f}°C, bề mặt tích tụ nhiệt độ rất cao, nguy cơ đảo nhiệt bề mặt mạnh.'
    elif indicator == 'NDVI':
        if val >= 0.45:
            return 'status-low', f'Thảm xanh dồi dào ({val:.3f})', f'Độ phủ thực vật cao (NDVI {val:.3f}), khả năng giữ ẩm và điều hòa vi khí hậu rất tốt.'
        elif val >= 0.30:
            return 'status-mid', f'Thảm xanh trung bình ({val:.3f})', f'Độ phủ thực vật ở mức trung bình đô thị (NDVI {val:.3f}), xen kẽ giữa mảng xanh và công trình.'
        else:
            return 'status-high', f'Thảm xanh suy giảm ({val:.3f})', f'Độ phủ thực vật thấp (NDVI {val:.3f}), mật độ bê tông hóa cao, thảm phủ xanh mỏng.'
    elif indicator == 'TVDI':
        if val < 0.40:
            return 'status-low', f'Độ ẩm dồi dào ({val:.3f})', f'Chỉ số hạn khô {val:.3f}, bề mặt duy trì độ ẩm tự nhiên tốt, độ bốc thoát hơi nước ổn định.'
        elif val <= 0.60:
            return 'status-mid', f'Khô hạn nhẹ ({val:.3f})', f'Chỉ số hạn khô {val:.3f}, bề mặt bắt đầu khô ráo, nguy cơ thiếu ẩm vi mô.'
        elif val <= 0.75:
            return 'status-high', f'Khô hạn vừa ({val:.3f})', f'Chỉ số hạn khô {val:.3f}, độ ẩm bề mặt suy giảm rõ rệt trong chu kỳ ít mưa.'
        else:
            return 'status-high', f'Khô hạn nghiêm trọng ({val:.3f})', f'Chỉ số hạn khô {val:.3f}, khô nóng cục bộ kéo dài, thảm cỏ và đất trống kiệt ẩm.'
    elif indicator == 'NO2':
        if val < 35.0:
            return 'status-low', f'NO₂ trong lành ({val:.1f})', f'Mật độ NO₂ đạt {val:.1f} µmol/m², khí thải phương tiện giao thông và công nghiệp ở mức thấp.'
        elif val <= 55.0:
            return 'status-mid', f'NO₂ trung bình ({val:.1f})', f'Mật độ NO₂ đạt {val:.1f} µmol/m², mức phát thải giao thông thường nhật tại các trục lộ đô thị.'
        elif val <= 75.0:
            return 'status-mid', f'NO₂ khá cao ({val:.1f})', f'Mật độ NO₂ đạt {val:.1f} µmol/m², lưu lượng giao thông tăng và tích tụ khí thải NOx.'
        else:
            return 'status-high', f'NO₂ gia tăng ({val:.1f})', f'Mật độ NO₂ đạt {val:.1f} µmol/m², nồng độ khí thải NOx tăng cao tại khu vực đông xe cộ và công nghiệp.'
    elif indicator == 'CO':
        if val < 30.0:
            return 'status-low', f'CO thấp ({val:.1f})', f'Hàm lượng CO cột khí quyển {val:.1f} mmol/m², không khí đối lưu thông thoáng.'
        elif val <= 38.0:
            return 'status-mid', f'CO trung bình ({val:.1f})', f'Hàm lượng CO cột khí quyển {val:.1f} mmol/m², ở mức thông thường của đô thị đông dân.'
        else:
            return 'status-high', f'CO cao ({val:.1f})', f'Hàm lượng CO cột khí quyển {val:.1f} mmol/m², tích tụ khí đốt nhiên liệu tăng cao.'
    elif indicator == 'AOD':
        if val < 0.20:
            return 'status-low', f'AOD thấp · Trời trong ({val:.3f})', f'Độ dày quang học sol khí {val:.3f}, bầu khí quyển quang đãng, nồng độ hạt bụi lơ lửng thấp.'
        elif val <= 0.30:
            return 'status-mid', f'AOD trung bình ({val:.3f})', f'Độ dày quang học sol khí {val:.3f}, tán xạ quang học sol khí ở mức vừa phải theo mùa.'
        elif val <= 0.40:
            return 'status-high', f'AOD khá cao · Bụi mù nhẹ ({val:.3f})', f'Độ dày quang học sol khí {val:.3f}, nồng độ hạt aerosol gia tăng, tầm nhìn giảm.'
        else:
            return 'status-high', f'AOD cao · Mù sol khí ({val:.3f})', f'Độ dày quang học sol khí {val:.3f}, mật độ hạt aerosol dày đặc, bầu trời mờ đục.'
    return 'status-mid', 'Bình thường', f'Giá trị {indicator} là {val:.3f}.'


def get_sensor_info(indicator, mode_str, month_str, bad_months):
    """Thông tin nguồn cảm biến viễn thám và tình trạng chất lượng dữ liệu."""
    if indicator in LANDSAT:
        sensor = 'Landsat 8/9 (TIRS & OLI)'
        is_bad = month_str in bad_months
        if mode_str.startswith('Lịch sử'):
            if is_bad:
                quality = 'Nội suy (không có ảnh sạch mây)'
                quality_cls = 'status-mid'
            else:
                quality = 'Ảnh quan sát thật (1 km)'
                quality_cls = 'status-low'
        else:
            quality = 'Mô hình XGBoost vi khí hậu'
            quality_cls = 'status-cyan'
    elif indicator in {'NO2', 'CO'}:
        sensor = 'Sentinel-5P (TROPOMI khí quyển)'
        quality = 'Quan sát hàng ngày' if mode_str.startswith('Lịch sử') else 'Mô hình XGBoost dự báo'
        quality_cls = 'status-low' if mode_str.startswith('Lịch sử') else 'status-cyan'
    else:  # AOD
        sensor = 'MODIS (MAIAC 1 km)'
        quality = 'Quan sát MODIS 1 km' if mode_str.startswith('Lịch sử') else 'Mô hình XGBoost dự báo'
        quality_cls = 'status-low' if mode_str.startswith('Lịch sử') else 'status-cyan'
    return sensor, quality, quality_cls


def generate_forecast_notes(indicator, dist, month_str, forecast_frame):
    """Tạo nhận định tự động đa chỉ số cho tab Dự báo."""
    cur = forecast_frame[forecast_frame.date.dt.strftime('%Y-%m') == month_str]
    if cur.empty:
        cur = forecast_frame.iloc[[0]]
    fc_val = float(cur.forecast.iloc[0])
    clim_val = float(cur.climatology.iloc[0])
    diff = fc_val - clim_val
    diff_pct = ((fc_val / clim_val) - 1) * 100 if clim_val != 0 else np.nan
    prec = display_precision(indicator)
    u = IND[indicator][1]
    u_str = f' {u}' if u else ''
    
    notes = []
    dir_str = "cao hơn" if diff > 0 else "thấp hơn"
    threshold = 0.001 if indicator in {'UTFVI', 'NDVI', 'TVDI', 'AOD'} else 0.2
    if abs(diff) < threshold:
        notes.append(f"Dự báo {indicator} tháng {month_str} tại {dist} xấp xỉ mức khí hậu chuẩn ({fc_val:.{prec}f}{u_str} so với {clim_val:.{prec}f}{u_str}).")
    else:
        notes.append(f"Dự báo {indicator} tháng {month_str} tại {dist} đạt {fc_val:.{prec}f}{u_str}, {dir_str} mức khí hậu tham chiếu {abs(diff):.{prec}f}{u_str} ({diff_pct:+.1f}%).")
        
    if indicator == 'UTFVI':
        notes.append("Giai đoạn cuối năm (tháng 9–12) vi khí hậu TP.HCM chuyển dần từ cuối mùa mưa sang đầu mùa khô. Áp lực đảo nhiệt có xu hướng ổn định tại khu vực có độ che phủ thực vật cao, trong khi khu vực trung tâm và đô thị hóa nhanh vẫn duy trì mức đảo nhiệt trung bình – mạnh.")
    elif indicator == 'LST':
        notes.append("Nhiệt độ bề mặt (LST) tháng 9–11 chịu ảnh hưởng của các đợt mưa cuối mùa giúp hạ nhiệt bề mặt; bước sang tháng 12 khi mùa khô bắt đầu, biên độ dao động nhiệt ngày đêm có xu hướng tăng.")
    elif indicator == 'NDVI':
        notes.append("Chỉ số thực vật (NDVI) duy trì độ xanh tươi vào cuối mùa mưa (tháng 9–10) nhờ lượng ẩm dồi dào, sau đó bắt đầu giảm nhẹ vào tháng 11–12 khi thảm cỏ và cây xanh bước vào chu kỳ hanh khô.")
    elif indicator == 'TVDI':
        notes.append("Chỉ số hạn khô (TVDI) phản ánh độ ẩm đất và thảm phủ. Giá trị thấp trong các tháng mưa (9–10) phản ánh tình trạng ẩm ướt, và có xu hướng tăng vào tháng 12 khi lượng mưa suy giảm rõ rệt.")
    elif indicator == 'NO2':
        notes.append("Mật độ NO₂ thường gia tăng vào các tháng cuối năm (10–12) do lưu lượng phương tiện vận tải tăng cao phục vụ sản xuất – tiêu dùng mùa lễ Tết và hiện tượng nghịch nhiệt khí quyển vào sáng sớm.")
    elif indicator == 'CO':
        notes.append("Nồng độ CO cột khí quyển thể hiện mức độ phát thải từ quá trình đốt cháy nhiên liệu giao thông và sản xuất. Xu hướng cuối năm phụ thuộc vào tốc độ gió đối lưu bề mặt và phân tán khí quyển.")
    elif indicator == 'AOD':
        notes.append("Độ dày quang học sol khí (AOD) phản ánh bụi mịn và hạt lơ lửng. Tháng 9–10 mưa thường rửa trôi hạt sol khí (AOD thấp), sang tháng 11–12 thời tiết ít mưa và khí quyển ổn định có thể làm AOD gia tăng.")
    return notes

# ---------------- THANH BÊN ----------------
st.sidebar.title('Bộ lọc')
mode = st.sidebar.radio('Chế độ xem', ['Lịch sử 2020-2026', 'Dự báo 9-12/2026'], index=1)
ind = st.sidebar.selectbox('Lớp dữ liệu', list(IND), index=list(IND).index('AOD'),
                           format_func=lambda k: IND[k][0])
district = st.sidebar.selectbox('Khu vực', [ALL] + districts)
name, unit = IND[ind]
unit_txt = f' ({unit})' if unit else ''

if mode.startswith('Lịch sử'):
    months = sorted(hist.date.dt.strftime('%Y-%m').unique())
    month = st.sidebar.select_slider('Tháng', options=months, value=months[-1])
    only_obs = st.sidebar.checkbox('Chỉ hiển thị ô có ảnh Landsat quan sát thật', value=False,
                                   disabled=ind not in LANDSAT) and ind in LANDSAT
    if ind in LANDSAT and month in BAD:
        st.sidebar.warning('Tháng này không có ảnh Landsat đáng tin cậy: giá trị là nội suy.')
else:
    fmonths = sorted(fc.date.dt.strftime('%Y-%m').unique())
    month = st.sidebar.select_slider('Tháng dự báo', options=fmonths, value=fmonths[min(1, len(fmonths) - 1)])
    view = st.sidebar.radio('Hiển thị', ['Dự báo', 'Khí hậu theo tháng', 'Chênh (dự báo - khí hậu)'])
    only_obs = False

scale_mode = st.sidebar.radio(
    'Thang màu bản đồ',
    ['Tự động theo tháng hiện tại', 'Cố định toàn kỳ 2020–2026'],
    index=0,
    help='Tự động: Tự điều chỉnh min–max theo dữ liệu tháng và khu vực đang chọn. Cố định: Dùng dải đo chuẩn 2020–2026. Chế độ chênh lệch luôn dùng thang đối xứng quanh 0.',
    disabled=mode.startswith('Dự báo') and view.startswith('Chênh')
)

glo_lo, glo_hi = hist[ind].quantile([0.02, 0.98]).tolist()
lo, hi = glo_lo, glo_hi

if mode.startswith('Lịch sử'):
    export_df = hist[hist.date.dt.strftime('%Y-%m') == month].copy()
    if only_obs:
        export_df.loc[~export_df.observed, ind] = np.nan
    export_df['val'] = export_df[ind]
else:
    export_df = fc[(fc.indicator == ind) & (fc.date.dt.strftime('%Y-%m') == month)].copy()
    if view == 'Dự báo':
        export_df['val'] = export_df.forecast
    elif view == 'Khí hậu theo tháng':
        export_df['val'] = export_df.climatology
    else:
        export_df['val'] = export_df.forecast - export_df.climatology
if district != ALL:
    export_df = export_df[export_df.district_vi == district]
report = export_df[['cell_id', 'district_vi', 'lon', 'lat', 'val']].rename(
    columns={'cell_id': 'Mã ô lưới', 'district_vi': 'Quận/huyện', 'lon': 'Kinh độ', 'lat': 'Vĩ độ', 'val': 'Giá trị'})
report.insert(0, 'Tháng', month)
report.insert(1, 'Chỉ số', f'{ind} · {name}')
report.insert(2, 'Chế độ', 'Lịch sử' if mode.startswith('Lịch sử') else view)

# Tính toán các chỉ số đồng bộ cho Thanh trạng thái
precision = display_precision(ind)
unit_suffix = f' {unit}' if unit else ''
current_avg = float(export_df['val'].mean())
is_anomaly_view = mode.startswith('Dự báo') and view.startswith('Chênh')
if is_anomaly_view:
    st_cls = 'status-cyan'
    if pd.isna(current_avg):
        st_label, st_desc = 'Chưa có dữ liệu', 'Chưa đủ dữ liệu để tính chênh lệch so với khí hậu tham chiếu.'
    elif current_avg > 0:
        st_label = f'Cao hơn khí hậu ({current_avg:+.{display_precision(ind)}f}{unit_suffix})'
        st_desc = 'Giá trị đang xem là chênh lệch dự báo trừ khí hậu; số dương nghĩa là cao hơn mức khí hậu tham chiếu, không phải giá trị tuyệt đối của chỉ số.'
    elif current_avg < 0:
        st_label = f'Thấp hơn khí hậu ({current_avg:+.{display_precision(ind)}f}{unit_suffix})'
        st_desc = 'Giá trị đang xem là chênh lệch dự báo trừ khí hậu; số âm nghĩa là thấp hơn mức khí hậu tham chiếu, không phải giá trị tuyệt đối của chỉ số.'
    else:
        st_label = 'Bằng mức khí hậu (0)'
        st_desc = 'Dự báo bằng mức khí hậu tham chiếu; bản đồ đang thể hiện độ lệch quanh mốc 0.'
else:
    st_cls, st_label, st_desc = evaluate_indicator_status(ind, current_avg)
sensor_name, sensor_quality, sensor_quality_cls = get_sensor_info(ind, mode, month, BAD)

hero_delta_html = ''
if mode.startswith('Dự báo') and view == 'Dự báo' and 'climatology' in export_df.columns:
    clim_avg = float(export_df['climatology'].mean())
    fc_diff = current_avg - clim_avg
    diff_dir = 'cao hơn' if fc_diff > 0 else 'thấp hơn'
    hero_delta_html = f'<span class="hero-tag">Chênh lệch khí hậu: <strong>{fc_diff:+.{precision}f}{unit_suffix}</strong> ({diff_dir})</span>'
elif mode.startswith('Lịch sử'):
    months_list = sorted(hist.date.dt.strftime('%Y-%m').unique())
    m_idx = months_list.index(month) if month in months_list else -1
    if m_idx > 0:
        prev_m = months_list[m_idx - 1]
        prev_df = hist[hist.date.dt.strftime('%Y-%m') == prev_m]
        if district != ALL:
            prev_df = prev_df[prev_df.district_vi == district]
        prev_avg = float(prev_df[ind].mean())
        m_diff = current_avg - prev_avg
        m_dir = 'tăng' if m_diff > 0 else 'giảm'
        hero_delta_html = f'<span class="hero-tag">So tháng trước ({prev_m}): <strong>{m_diff:+.{precision}f}{unit_suffix}</strong> ({m_dir})</span>'

hero_left, hero_right = st.columns([6.3, 2], vertical_alignment='bottom')
hero_title = name
if name.endswith(f' ({ind})'):
    hero_title = f'{name[:-(len(ind) + 3)]} <span>({ind})</span>'
with hero_left:
    mode_text = 'Dữ liệu lịch sử 2020–2026' if mode.startswith('Lịch sử') else f'Dự báo mô hình ({view})'
    st.markdown(
        f'<div class="page-hero"><div><div class="hero-kicker">Environment intelligence · TP. Hồ Chí Minh</div>'
        f'<div class="hero-title">{hero_title}</div>'
        f'<div class="hero-subtitle">{month} &nbsp;·&nbsp; {district} &nbsp;·&nbsp; {mode_text}</div>'
        f'<div class="hero-tag-list">'
        f'<span class="status-pill {st_cls}">{st_label}</span>'
        f'<span class="hero-tag">Trung bình: <strong>{current_avg:.{precision}f}{unit_suffix}</strong></span>'
        f'{hero_delta_html}'
        f'</div></div>'
        '<div class="brand-status"><i></i> ENVISAT LIVE</div></div>', unsafe_allow_html=True)
with hero_right:
    st.download_button('↓  Xuất báo cáo CSV', data=report.to_csv(index=False).encode('utf-8-sig'),
                       file_name=f'{ind}_{month}.csv', mime='text/csv', width='stretch')

st.markdown(
    '<div class="insight-banner"><div class="insight-icon">ℹ</div><div class="insight-copy">'
    '<div class="insight-header">'
    f'<span class="status-pill {st_cls}">{st_label}</span>'
    f'<span class="status-pill status-cyan">Nguồn: {sensor_name}</span>'
    f'<span class="status-pill {sensor_quality_cls}">{sensor_quality}</span>'
    '</div>'
    f'<strong>Hiện trạng {name} tại {district} (Tháng {month})</strong>'
    f'<p>{st_desc}</p>'
    '</div></div>', unsafe_allow_html=True)


# ---------------- HÀM VẼ BẢN ĐỒ ----------------
def make_map(df, cmap=None, classes=False, diverging=False, caption='', scale_label=''):
    """df: cell_id, lon, lat, district_vi, val, (cls)."""
    dx, dy = 0.00457, 0.00452
    precision = display_precision(ind)
    m = folium.Map(location=[df.lat.mean(), df.lon.mean()], zoom_start=10,
                   tiles='OpenStreetMap', control_scale=True)
    m.get_root().header.add_child(folium.Element(
        '<style>.leaflet-tile-pane { filter:invert(1) hue-rotate(180deg) brightness(.62) saturate(.65); }</style>'))
    for r in df.itertuples():
        if pd.isna(r.val):
            continue
        inside = (district == ALL) or (r.district_vi == district)
        if classes:
            if pd.isna(r.cls):
                continue
            k = int(np.clip(r.cls, 1, 6)) - 1
            color, txt = CLASS_COLORS[k], f'{CLASS_NAMES[k]} (UTFVI {r.val:.4f})'
        else:
            color, txt = cmap(r.val), f'{r.val:.{precision}f}{unit_txt}'
        folium.Rectangle(bounds=[[r.lat - dy, r.lon - dx], [r.lat + dy, r.lon + dx]], weight=0, fill=True,
                         fill_color=color, fill_opacity=0.85 if inside else 0.15,
                         tooltip=f'{r.district_vi} - {txt}').add_to(m)

    sub = df if district == ALL else df[df.district_vi == district]
    sub = sub.dropna(subset=['lat', 'lon'])
    if sub.empty:
        sub = df.dropna(subset=['lat', 'lon'])
    target_bounds = [[float(sub.lat.min() - dy), float(sub.lon.min() - dx)],
                     [float(sub.lat.max() + dy), float(sub.lon.max() + dx)]]
    m.fit_bounds(target_bounds, padding=(28, 28), max_zoom=12 if district != ALL else 10)

    m.get_root().header.add_child(folium.Element('''
    <style>
      .map-locate-control { display:flex; align-items:center; gap:7px; margin-top:5px; padding:7px 10px;
        border:1px solid #28516b; border-radius:8px; background:#0b1929ee; color:#dceaf7;
        box-shadow:0 4px 14px #02091488; cursor:pointer; font:600 11px 'Be Vietnam Pro',sans-serif;
        transition:background .18s ease,border-color .18s ease,transform .18s ease; }
      .map-locate-control span:first-child { color:#16c8f4; font-size:17px; line-height:12px; }
      .map-locate-control:hover,.map-locate-control.is-active { border-color:#16c8f4; background:#10334a; color:#fff; transform:translateY(-1px); }
      .map-legend { position:fixed; top:14px; right:14px; z-index:9999; width:min(350px,calc(100% - 78px));
        box-sizing:border-box; padding:12px 14px 11px; border:1px solid #31516d; border-radius:11px;
        background:rgba(8,20,34,.96); color:#e7f1fb; box-shadow:0 8px 24px #02091499;
        font-family:'Be Vietnam Pro',sans-serif; backdrop-filter:blur(8px); }
      .map-legend-title { margin:0 0 3px; color:#f1f8ff; font-size:12.5px; line-height:1.35; font-weight:700; }
      .map-legend-meta { display:flex; justify-content:space-between; align-items:center; margin-bottom:7px; font-size:10px; color:#8fa6bd; }
      .map-legend-badge { display:inline-block; padding:1px 6px; border-radius:4px; font-size:9.5px; font-weight:600; background:#102b40; color:#16c8f4; border:1px solid #165b7d; }
      .map-legend-ticks { display:flex; justify-content:space-between; gap:4px; margin-bottom:5px; }
      .map-legend-ticks span { color:#e0edf8; font-size:10.5px; line-height:1.2; font-weight:600; font-variant-numeric:tabular-nums; }
      .map-legend-gradient { height:12px; border:1px solid #c5d7e588; border-radius:99px; box-shadow:inset 0 0 0 1px #06101c55; }
      .map-legend-labels { display:flex; justify-content:space-between; margin-top:5px; font-size:9.5px; color:#95acca; font-weight:600; }
      .map-legend-unit { margin-top:5px; color:#8fa6bd; text-align:right; font-size:9.5px; }
      .map-legend-classes { display:grid; grid-template-columns:1fr; gap:5px; margin-top:6px; }
      .map-legend-class { display:flex; align-items:center; justify-content:space-between; gap:7px; color:#d2e1ef; font-size:10.5px; }
      .map-legend-class-left { display:flex; align-items:center; gap:7px; }
      .map-legend-swatch { width:10px; height:10px; flex:none; border:1px solid #ffffff55; border-radius:3px; }
      .map-legend-pct { color:#16c8f4; font-weight:700; font-size:10px; font-variant-numeric:tabular-nums; }
      @media(max-width:600px) { .map-legend { top:10px; right:10px; width:min(280px,calc(100% - 68px)); padding:10px 11px; }
        .map-legend-title { font-size:11.5px; } .map-legend-ticks span { font-size:9.5px; }
        .map-locate-label { display:none; } }
    </style>'''))
    locate_control = MacroElement()
    locate_control.bounds = json.dumps(target_bounds)
    locate_control.max_zoom = 12 if district != ALL else 10
    locate_control.label = json.dumps(f'Đưa bản đồ về {district}', ensure_ascii=False)
    locate_control._template = Template('''
    {% macro script(this, kwargs) %}
      var locateControl = L.control({position: 'topleft'});
      locateControl.onAdd = function () {
        var button = L.DomUtil.create('button', 'map-locate-control');
        button.type = 'button';
        button.title = {{ this.label }};
        button.setAttribute('aria-label', button.title);
        button.innerHTML = '<span aria-hidden="true">⌖</span><span class="map-locate-label">Tới khu vực</span>';
        L.DomEvent.disableClickPropagation(button);
        L.DomEvent.on(button, 'click', function () {
          {{ this._parent.get_name() }}.fitBounds({{ this.bounds }},
            {padding: [28, 28], maxZoom: {{ this.max_zoom }}, animate: true});
          button.classList.add('is-active');
          setTimeout(function () { button.classList.remove('is-active'); }, 850);
        });
        return button;
      };
      locateControl.addTo({{ this._parent.get_name() }});
    {% endmacro %}
    ''')
    locate_control.add_to(m)

    scale_badge_html = f'<span class="map-legend-badge">{html.escape(scale_label)}</span>' if scale_label else ''
    meta_html = f'<div class="map-legend-meta"><span>{month} · {district}</span>{scale_badge_html}</div>'

    if classes:
        valid_cls = scope(df)['cls'].dropna()
        total_cls = len(valid_cls)
        class_pcts = {k: ((valid_cls == k).mean() * 100 if total_cls > 0 else 0.0) for k in range(1, 7)}
        th = meta['utfvi_thresholds']
        class_ranges = [
            '≤ 0',
            f'0 – {th[1]}',
            f'{th[1]} – {th[2]}',
            f'{th[2]} – {th[3]}',
            f'{th[3]} – {th[4]}',
            f'> {th[4]}'
        ]
        items = ''.join(
            f'<div class="map-legend-class">'
            f'<div class="map-legend-class-left"><span class="map-legend-swatch" style="background:{c};"></span>'
            f'<span>{html.escape(str(n))} <small style="color:#8ba3bc;">({class_ranges[i]})</small></span></div>'
            f'<span class="map-legend-pct">{class_pcts[i + 1]:.1f}%</span>'
            f'</div>'
            for i, (c, n) in enumerate(zip(CLASS_COLORS, CLASS_NAMES))
        )
        m.get_root().html.add_child(folium.Element(
            f'<div class="map-legend"><div class="map-legend-title">Mức cảnh báo UTFVI</div>'
            f'{meta_html}'
            f'<div class="map-legend-classes">{items}</div></div>'))
    else:
        tick_values = np.linspace(float(cmap.vmin), float(cmap.vmax), 5)
        ticks = ''.join(f'<span>{value:.{precision}f}</span>' for value in tick_values)
        color_stops = ', '.join(
            f'{cmap.rgb_hex_str(float(cmap.vmin) + (float(cmap.vmax) - float(cmap.vmin)) * i / 32)} {i * 100 / 32:.1f}%'
            for i in range(33))
        unit_label = html.escape(unit if unit else 'Không thứ nguyên')
        legend_title = html.escape(caption)

        if diverging:
            labels_html = ('<div class="map-legend-labels">'
                           '<span>◀ Thấp hơn khí hậu</span><span>Chuẩn (0)</span><span>Cao hơn khí hậu ▶</span></div>')
        else:
            low_text, high_text = LEVEL_SEMANTICS.get(ind, ('Thấp', 'Cao'))
            labels_html = (f'<div class="map-legend-labels">'
                           f'<span>◀ Thấp ({low_text})</span><span>Trung bình</span><span>Cao ({high_text}) ▶</span></div>')

        m.get_root().html.add_child(folium.Element(
            f'<div class="map-legend"><div class="map-legend-title">{legend_title}</div>'
            f'{meta_html}'
            f'<div class="map-legend-ticks">{ticks}</div>'
            f'<div class="map-legend-gradient" style="background:linear-gradient(90deg,{color_stops});"></div>'
            f'{labels_html}'
            f'<div class="map-legend-unit">Đơn vị: {unit_label}</div></div>'))
    return m


def colormap_for(vmin, vmax, div=False):
    if div:
        return LinearColormap(colors=list(reversed(linear.RdBu_11.colors)), vmin=-vmax, vmax=vmax)
    return CMAPS[ind].scale(vmin, vmax)


def automatic_color_limits(frame):
    """Tính thang màu theo dữ liệu đang xem, chỉ trong khu vực được chọn."""
    values = scope(frame)['val'].dropna()
    if values.empty:
        return glo_lo, glo_hi
    c_lo, c_hi = (float(value) for value in values.quantile([0.01, 0.99]))
    if c_lo >= c_hi:
        c_lo, c_hi = float(values.min()), float(values.max())
    if c_lo >= c_hi:
        padding = max(abs(c_lo) * 0.01, 1e-4)
        c_lo, c_hi = c_lo - padding, c_hi + padding
    return c_lo, c_hi


def scope(df):
    return df if district == ALL else df[df.district_vi == district]


def chart_theme(chart):
    return chart.configure(
        background='#0b1929',
        view={'stroke': 'transparent'},
        axis={'labelColor': '#91a4ba', 'titleColor': '#c6d7e7', 'gridColor': '#1b3047',
              'domainColor': '#28415a', 'tickColor': '#28415a', 'labelFont': 'Be Vietnam Pro',
              'titleFont': 'Be Vietnam Pro'},
        legend={'labelColor': '#a6b7ca', 'titleColor': '#dceaf7', 'labelFont': 'Be Vietnam Pro',
                'titleFont': 'Be Vietnam Pro'})


def render_table(frame, badge_columns=(), highlight_column=None, highlight_value=None):
    """Render a responsive, dark-themed HTML table without Streamlit's white grid canvas."""
    headers = ''.join(f'<th>{html.escape(str(column))}</th>' for column in frame.columns)
    rows = []
    for row_index, row in enumerate(frame.itertuples(index=False, name=None)):
        cells = []
        for column, value in zip(frame.columns, row):
            if pd.isna(value):
                text = '—'
            elif isinstance(value, (float, np.floating)):
                if column.startswith('Chỉ số') or column.startswith('Chênh'):
                    precision = display_precision(ind)
                elif column in {'RMSE mô hình', 'RMSE khí hậu', 'RMSE (theo ô)', 'MAE (theo ô)'}:
                    precision = 4
                elif column in {'So khí hậu (%)', 'Cải thiện (%)'}:
                    precision = 2
                else:
                    precision = 4
                text = f'{value:,.{precision}f}'
            elif isinstance(value, (int, np.integer)):
                text = f'{value:,}'
            else:
                text = str(value)
            safe_text = html.escape(text)
            if column in badge_columns:
                css_class = badge_columns[column].get(text, 'status-mid')
                content = f'<span class="status-pill {css_class}">{safe_text}</span>'
            elif column == 'Xếp hạng':
                rank_class = ' is-top' if row_index == 0 else ''
                content = f'<span class="rank-number{rank_class}">{safe_text}</span>'
            elif column.startswith('Chỉ số') or column.startswith('Chênh') or column in (
                    'Trung bình', 'Dự báo mô hình', 'Khí hậu', 'RMSE mô hình', 'RMSE khí hậu',
                    'RMSE (theo ô)', 'MAE (theo ô)', 'So khí hậu (%)', 'Cải thiện (%)'):
                content = f'<span class="num">{safe_text}</span>'
            else:
                content = safe_text
            cells.append(f'<td>{content}</td>')
        row_class = ' class="is-selected"' if (
            highlight_column in frame.columns and row[frame.columns.get_loc(highlight_column)] == highlight_value
        ) else ''
        rows.append(f'<tr{row_class}>{"".join(cells)}</tr>')
    st.markdown(
        f'<div class="table-shell"><table class="dark-table"><thead><tr>{headers}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>', unsafe_allow_html=True)


def section_title(title, subtitle):
    st.markdown(
        f'<div class="section-title"><div><h2>{html.escape(title)}</h2>'
        f'<p>{html.escape(subtitle)}</p></div></div>', unsafe_allow_html=True)


tab_map, tab_hist, tab_fc, tab_val, tab_about = st.tabs(
    ['Bản đồ', 'Biểu đồ lịch sử', 'Dự báo', 'Kiểm định 2026', 'Giới thiệu và hạn chế'])

# ---------------- TAB 1: BẢN ĐỒ ----------------
with tab_map:
    st.markdown('<div class="panel-heading"><h2>Phân bố không gian</h2><span>Giá trị trung bình theo khu vực hành chính</span></div>',
                unsafe_allow_html=True)
    if mode.startswith('Lịch sử'):
        df = hist[hist.date.dt.strftime('%Y-%m') == month].copy()
        if only_obs:
            df.loc[~df.observed, ind] = np.nan
        df['val'] = df[ind]
        df['cls'] = df.UTFVI_class
        cap = f'{name}{unit_txt}'
        if ind == 'UTFVI':
            m = make_map(df, cmap=None, classes=True, caption=cap, scale_label='Phân cấp UTFVI')
        else:
            if scale_mode == 'Tự động theo tháng hiện tại':
                c_lo, c_hi = automatic_color_limits(df)
                s_lbl = f'Động tháng {month}'
            else:
                c_lo, c_hi = glo_lo, glo_hi
                s_lbl = 'Chuẩn 2020–2026'
            cmap = colormap_for(c_lo, c_hi)
            m = make_map(df, cmap=cmap, classes=False, caption=cap, scale_label=s_lbl)
    else:
        f = fc[(fc.indicator == ind) & (fc.date.dt.strftime('%Y-%m') == month)].copy()
        hz = int(f.horizon.iloc[0])
        selected_rel = rel[(rel.indicator == ind) & (rel.horizon == hz)].iloc[0]
        skill_pct, reliability_label = reliability_summary(
            selected_rel.rmse_model, selected_rel.rmse_climatology)
        if view == 'Dự báo':
            f['val'] = f.forecast
            value_description = 'Dự báo mô hình'
        elif view == 'Khí hậu theo tháng':
            f['val'] = f.climatology
            value_description = 'Khí hậu tham chiếu'
        else:
            f['val'] = f.forecast - f.climatology
            value_description = 'Chênh lệch dự báo − khí hậu'
        if ind == 'UTFVI' and view == 'Dự báo':
            f['cls'] = f.UTFVI_class
        elif ind == 'UTFVI' and view == 'Khí hậu theo tháng':
            f['cls'] = classify_utfvi(f['val'])
        else:
            f['cls'] = np.nan
        skill_text = (f'{skill_pct:+.1f}% RMSE (số âm nghĩa là tốt hơn khí hậu)'
                  if pd.notna(skill_pct) else 'Chưa đủ dữ liệu để đánh giá')
        st.info(f'Đang xem **{value_description} · {name} · {month} · {district}**. '
            f'Tầm dự báo: **{hz} tháng**; độ tin cậy mô hình toàn thành phố tại thời hạn này: '
            f'**{reliability_label}** ({skill_text}).')
        if view.startswith('Chênh'):
            anomaly_values = scope(f)['val'].dropna().abs()
            mx = float(anomaly_values.quantile(0.99)) if not anomaly_values.empty else 0.0
            if not np.isfinite(mx) or mx <= 0:
                mx = float(anomaly_values.max()) if not anomaly_values.empty else 0.0
            mx = max(mx, 1e-6)
            m = make_map(f, cmap=colormap_for(0, mx, div=True), diverging=True, caption=f'Chênh {name}{unit_txt}', scale_label='Chênh lệch khí hậu')
        elif ind == 'UTFVI':
            m = make_map(f, cmap=None, classes=True, caption=f'{name}{unit_txt}', scale_label='Phân cấp UTFVI')
        else:
            if scale_mode == 'Tự động theo tháng hiện tại':
                c_lo, c_hi = automatic_color_limits(f)
                s_lbl = f'Động tháng {month}'
            else:
                c_lo, c_hi = glo_lo, glo_hi
                s_lbl = 'Chuẩn 2020–2026'
            cmap = colormap_for(c_lo, c_hi)
            m = make_map(f, cmap=cmap, classes=False, caption=f'{name}{unit_txt}', scale_label=s_lbl)
        df = f
    st_folium(m, height=560, use_container_width=True, returned_objects=[],
              key=f"map_{ind}_{month}_{mode}_{district}_{scale_mode}_{view if not mode.startswith('Lịch sử') else 'hist'}")

    s_all = scope(df)
    s = s_all.val.dropna()
    c_all = df.val.dropna()
    precision = display_precision(ind)
    unit_suffix = f' {unit}' if unit else ''

    area_mean = float(s.mean()) if not s.empty else np.nan
    city_mean = float(c_all.mean()) if not c_all.empty else np.nan
    range_str = f'{s.min():.{precision}f} — {s.max():.{precision}f}{unit_suffix}' if not s.empty else '—'
    
    # Tính tỉ lệ ô cảnh báo / bất thường phù hợp với từng chỉ số
    if is_anomaly_view:
        alert_ratio = (s > 0).mean() * 100 if not s.empty else 0
        alert_label = 'Tỉ lệ ô cao hơn khí hậu'
        alert_val = f'{alert_ratio:.1f}%'
        alert_help = 'Tỉ lệ ô có chênh lệch dự báo − khí hậu dương; điều này chỉ có nghĩa là chỉ số cao hơn khí hậu tham chiếu, không đồng nghĩa mức ô nhiễm/nhiệt cao.'
    elif ind == 'UTFVI' and 'cls' in s_all.columns:
        alert_ratio = (s_all['cls'].dropna() >= 4).mean() * 100
        alert_label = 'Tỉ lệ ô cảnh báo nhiệt'
        alert_val = f'{alert_ratio:.1f}%'
        alert_help = 'Tỉ lệ ô lưới có mức sinh thái nhiệt Mạnh, Rất mạnh hoặc Cực mạnh (cấp 4–6)'
    elif ind == 'LST':
        alert_ratio = (s > 38.0).mean() * 100
        alert_label = 'Tỉ lệ ô nhiệt rất cao (>38°C)'
        alert_val = f'{alert_ratio:.1f}%'
        alert_help = 'Tỉ lệ ô lưới có nhiệt độ bề mặt trên 38°C, khớp với ngưỡng “Nhiệt độ rất cao” trong phân loại chỉ số.'
    elif ind == 'NDVI':
        alert_ratio = (s < 0.30).mean() * 100
        alert_label = 'Tỉ lệ ô thảm xanh thấp (<0.30)'
        alert_val = f'{alert_ratio:.1f}%'
        alert_help = 'Tỉ lệ ô lưới có độ che phủ thực vật kém (NDVI < 0.30), nguy cơ bê tông hóa cao'
    elif ind == 'TVDI':
        alert_ratio = (s >= 0.60).mean() * 100
        alert_label = 'Tỉ lệ ô hạn vừa – nặng'
        alert_val = f'{alert_ratio:.1f}%'
        alert_help = 'Tỉ lệ ô lưới có chỉ số hạn khô TVDI ≥ 0.60'
    elif ind == 'NO2':
        alert_ratio = (s > 75.0).mean() * 100
        alert_label = 'Tỉ lệ ô NO₂ cao (>75)'
        alert_val = f'{alert_ratio:.1f}%'
        alert_help = 'Tỉ lệ ô lưới có NO₂ trên 75 µmol/m², khớp với ngưỡng “NO₂ gia tăng” trong phân loại chỉ số.'
    elif ind == 'CO':
        alert_ratio = (s > 38.0).mean() * 100
        alert_label = 'Tỉ lệ ô CO cao (>38)'
        alert_val = f'{alert_ratio:.1f}%'
        alert_help = 'Tỉ lệ ô lưới có hàm lượng CO trên 38 mmol/m², khớp với ngưỡng “CO cao” trong phân loại chỉ số.'
    elif ind == 'AOD':
        alert_ratio = (s > 0.30).mean() * 100
        alert_label = 'Tỉ lệ ô sol khí cao (>0.30)'
        alert_val = f'{alert_ratio:.1f}%'
        alert_help = 'Tỉ lệ ô lưới có AOD trên 0.30, khớp với ngưỡng “AOD khá cao” trong phân loại chỉ số.'
    else:
        q75 = float(c_all.quantile(0.75)) if not c_all.empty else 0
        alert_ratio = (s >= q75).mean() * 100 if not s.empty else 0
        alert_label = 'Tỉ lệ ô nhóm cao (≥P75)'
        alert_val = f'{alert_ratio:.1f}%'
        alert_help = 'Tỉ lệ ô lưới nằm trong nhóm 25% giá trị cao nhất toàn thành phố'

    cell_count = len(s)
    total_cells = len(c_all)
    pct_coverage = (cell_count / max(total_cells, 1)) * 100

    if district == ALL:
        c1, c2, c3, c4 = st.columns(4)
        c1_delta = None
        if mode.startswith('Dự báo') and view == 'Dự báo' and 'climatology' in df.columns:
            c1_clim = float(df['climatology'].dropna().mean())
            c1_delta = f'{city_mean - c1_clim:+.{precision}f}{unit_suffix} so với khí hậu'
        elif mode.startswith('Lịch sử') and hero_delta_html:
            months_list = sorted(hist.date.dt.strftime('%Y-%m').unique())
            m_idx = months_list.index(month) if month in months_list else -1
            if m_idx > 0:
                prev_m = months_list[m_idx - 1]
                prev_val = float(hist[hist.date.dt.strftime('%Y-%m') == prev_m][ind].dropna().mean())
                c1_delta = f'{city_mean - prev_val:+.{precision}f}{unit_suffix} so với {prev_m}'

        c1.metric('Trung bình toàn TP', f'{city_mean:.{precision}f}{unit_suffix}', delta=c1_delta)
        c2.metric('Biên độ dao động (Min — Max)', range_str)
        c3.metric(alert_label, alert_val, help=alert_help)
        c4.metric('Số ô có dữ liệu', f'{cell_count:,} ô', delta='100% lưới TP', delta_color='off')
    else:
        c1, c2, c3, c4 = st.columns(4)
        diff_vs_city = area_mean - city_mean
        c1.metric(f'Trung bình {district}', f'{area_mean:.{precision}f}{unit_suffix}',
                  delta=f'{diff_vs_city:+.{precision}f}{unit_suffix} so với toàn TP')
        c2.metric('Trung bình toàn thành phố', f'{city_mean:.{precision}f}{unit_suffix}')
        c3.metric(alert_label, alert_val, help=alert_help)
        c4.metric(f'Biên độ {district}', range_str, delta=f'{cell_count:,} ô ({pct_coverage:.1f}% TP)', delta_color='off')

    st.markdown('<div class="panel-heading"><h2>Xếp hạng quận / huyện</h2><span>So sánh các khu vực nổi bật</span></div>',
                unsafe_allow_html=True)
    valid_df = df[df.val.notna()].copy()
    g = valid_df.groupby('district_vi').agg(trung_binh=('val', 'mean'), so_o=('val', 'count'))
    show_cls = ind == 'UTFVI' and df.cls.notna().any()
    if show_cls:
        valid_classes = valid_df[valid_df.cls.notna()].copy()
        valid_classes['w'] = (valid_classes.cls >= 4).astype(float)
        g['ty_le_o_canh_bao_%'] = (valid_classes.groupby('district_vi').w.mean() * 100).round(1)
    g = g.sort_values('trung_binh', ascending=False).round(4).reset_index()
    g.columns = ['Khu vực', 'Trung bình', 'Số ô'] + (['Tỉ lệ ô mức Mạnh trở lên (%)'] if show_cls else [])
    total = len(g)
    rank_labels = []
    for rank in range(total):
        percentile = rank / max(total, 1)
        if percentile < .1:
            rank_labels.append('Rất cao')
        elif percentile < .35:
            rank_labels.append('Cao')
        elif percentile < .7:
            rank_labels.append('Trung bình')
        else:
            rank_labels.append('Thấp')
    g.insert(0, 'Xếp hạng', [f'{rank:02d}' for rank in range(1, total + 1)])
    g['Mức tương đối'] = rank_labels
    col_metric_name = f'Chênh {ind}' if (not mode.startswith('Lịch sử') and view.startswith('Chênh')) else f'Chỉ số {ind}'
    g = g.rename(columns={'Trung bình': col_metric_name})
    table_badges = {'Mức tương đối': rank_status_styles(ind)}
    if is_anomaly_view:
        table_badges = {'Mức tương đối': {level: 'status-cyan'
                                           for level in ['Rất cao', 'Cao', 'Trung bình', 'Thấp']}}

    if district != ALL:
        user_row = g[g['Khu vực'] == district]
        if not user_row.empty:
            user_rank = user_row['Xếp hạng'].iloc[0]
            user_val = user_row[col_metric_name].iloc[0]
            user_level = user_row['Mức tương đối'].iloc[0]
            st.markdown(
                f'<div class="callout">📍 Khu vực đang chọn: <strong>{district}</strong> '
                f'đang xếp hạng <strong>#{user_rank}/{total}</strong> '
                f'với giá trị trung bình <strong>{user_val:,.{precision}f}{unit_suffix}</strong> '
                f'(mức phân vị tương đối: <strong>{user_level}</strong>).</div>', unsafe_allow_html=True)

    render_table(g.head(5), badge_columns=table_badges,
                 highlight_column='Khu vực' if district != ALL else None,
                 highlight_value=district)
    if total > 5:
        with st.expander(f'Xem tất cả {total} quận / huyện'):
            render_table(g, badge_columns=table_badges,
                         highlight_column='Khu vực' if district != ALL else None,
                         highlight_value=district)
    if (g['Số ô'] <= 9).any():
        st.caption('Quận có ít ô lưới (dưới 10 ô) thì giá trị trung bình dao động mạnh hơn.')

# ---------------- TAB 2: LỊCH SỬ ----------------
with tab_hist:
    st.subheader(f'Biến động {name} theo thời gian')
    h = hist.copy()
    if only_obs:
        h.loc[~h.observed, ind] = np.nan
    h['ym'] = h.date.dt.to_period('M').dt.to_timestamp()
    city = h.groupby('ym')[ind].mean().rename(ALL)
    series = pd.DataFrame({ALL: city})
    if district != ALL:
        series[district] = h[h.district_vi == district].groupby('ym')[ind].mean()
    long = series.reset_index().melt('ym', var_name='Khu vực', value_name='Giá trị')
    line = alt.Chart(long).mark_line(point=True).encode(
        x=alt.X('ym:T', title='Tháng'), y=alt.Y('Giá trị:Q', title=f'{name}{unit_txt}', scale=alt.Scale(zero=False)),
        color='Khu vực:N', tooltip=['ym:T', 'Khu vực:N', alt.Tooltip('Giá trị:Q', format='.4f')])
    layers = [line]

    # Kết nối 4 tháng dự báo cuối năm 2026 bằng đường nét đứt cyan
    last_hist_date = h.ym.max()
    if district == ALL:
        last_hist_val = float(city.loc[last_hist_date])
        fc_target = fc[fc.indicator == ind].groupby('date')['forecast'].mean().reset_index()
    else:
        last_hist_val = float(series[district].loc[last_hist_date])
        fc_target = fc[(fc.indicator == ind) & (fc.district_vi == district)].groupby('date')['forecast'].mean().reset_index()
    fc_anchor = pd.DataFrame([{'date': last_hist_date, 'forecast': last_hist_val}])
    fc_ext = pd.concat([fc_anchor, fc_target]).reset_index(drop=True).rename(columns={'date': 'ym', 'forecast': 'Giá trị'})
    fc_ext['Loại'] = 'Dự báo 9–12/2026'

    fc_line = alt.Chart(fc_ext).mark_line(strokeDash=[4, 4], point=True, color='#16c8f4').encode(
        x='ym:T', y='Giá trị:Q',
        tooltip=['ym:T', alt.Tooltip('Giá trị:Q', format='.4f'), alt.Tooltip('Loại:N', title='Dữ liệu')]
    )
    layers.append(fc_line)

    if ind in LANDSAT:
        bad = pd.DataFrame({'ym': pd.to_datetime([b + '-01' for b in sorted(BAD)])})
        layers.append(alt.Chart(bad).mark_rule(color='gray', strokeDash=[3, 3], opacity=0.6).encode(x='ym:T'))
        if only_obs:
            st.caption('Đã loại các ô nội suy; đường gạch xám: tháng không có ảnh Landsat sạch mây; nét đứt cyan: 4 tháng dự báo cuối 2026.')
        else:
            st.caption('Đường gạch xám: tháng không có ảnh Landsat sạch mây (giá trị nội suy); nét đứt cyan: 4 tháng dự báo cuối 2026.')
    else:
        st.caption('Đường nét liền: quan trắc lịch sử 2020–08/2026; đường nét đứt cyan: 4 tháng dự báo 09–12/2026.')

    # Đánh dấu tháng đang chọn (hoạt động đồng bộ cả chế độ Lịch sử và Dự báo)
    selected_date = pd.DataFrame({'ym': [pd.Timestamp(f'{month}-01')]})
    layers.append(alt.Chart(selected_date).mark_rule(color='#f1f8ff', strokeWidth=2, opacity=.85).encode(x='ym:T'))
    st.altair_chart(chart_theme(alt.layer(*layers).properties(height=340)), width='stretch')

    st.subheader('So sánh các năm theo tháng')
    base = scope(h).assign(nam=lambda x: x.date.dt.year.astype(str), thang=lambda x: x.date.dt.month)
    yr = base.groupby(['nam', 'thang'])[ind].mean().reset_index()
    selected_year = month[:4]
    selected_calendar_month = int(month[-2:])
    ch = alt.Chart(yr).mark_line(point=True).encode(
        x=alt.X('thang:O', title='Tháng (1–12)'),
        y=alt.Y(f'{ind}:Q', title=f'{name}{unit_txt}', scale=alt.Scale(zero=False)),
        color=alt.Color('nam:N', title='Năm'),
        size=alt.condition(alt.datum.nam == selected_year, alt.value(3.5), alt.value(1.6)),
        opacity=alt.condition(alt.datum.nam == selected_year, alt.value(1.0), alt.value(0.55)),
        tooltip=['nam:N', 'thang:O', alt.Tooltip(f'{ind}:Q', format='.4f')])
    month_rule = alt.Chart(pd.DataFrame({'thang': [selected_calendar_month]})).mark_rule(
        color='#16c8f4', strokeWidth=2, opacity=.85).encode(x='thang:O')
    ch = alt.layer(ch, month_rule)
    st.altair_chart(chart_theme(ch.properties(height=320)), width='stretch')
    st.caption(f'Đường vẽ đậm làm nổi bật năm {selected_year} (tương ứng với tháng đang chọn); vạch cyan dọc đánh dấu tháng {selected_calendar_month}.')

# ---------------- TAB 3: DỰ BÁO ----------------
with tab_fc:
    section_title(f'Dự báo {name}', f'Lịch sử gần đây, dự báo và khí hậu tham chiếu · {district}')
    past = hist.assign(ym=hist.date.dt.to_period('M').dt.to_timestamp())
    if only_obs:
        past.loc[~past.observed, ind] = np.nan
    past = scope(past)
    past = past[past.ym >= past.ym.max() - pd.DateOffset(months=23)].groupby('ym')[ind].mean().reset_index()
    past.columns = ['ym', 'Giá trị']
    past['Loại'] = 'Lịch sử'

    ff = scope(fc[fc.indicator == ind]).groupby('date')[['horizon', 'forecast', 'lower', 'upper', 'climatology']].mean().reset_index()
    fcl = ff[['date', 'forecast']].rename(columns={'date': 'ym', 'forecast': 'Giá trị'})
    if not past.empty:
        last_hist_point = past.iloc[[-1]]
        fcl_anchor = pd.DataFrame([{'ym': last_hist_point['ym'].iloc[0], 'Giá trị': last_hist_point['Giá trị'].iloc[0]}])
        fcl = pd.concat([fcl_anchor, fcl]).reset_index(drop=True)
    fcl['Loại'] = 'Dự báo'

    clm = ff[['date', 'climatology']].rename(columns={'date': 'ym', 'climatology': 'Giá trị'})
    clm['Loại'] = 'Khí hậu'

    lines = pd.concat([past, fcl, clm])
    color = alt.Color('Loại:N', scale=alt.Scale(domain=['Lịch sử', 'Dự báo', 'Khí hậu'],
                                                range=['#7c9bb8', '#16c8f4', '#ffb648']))
    base_chart = alt.Chart(lines).mark_line(point=True).encode(
        x=alt.X('ym:T', title='Tháng'), y=alt.Y('Giá trị:Q', title=f'{name}{unit_txt}', scale=alt.Scale(zero=False)),
        color=color, strokeDash=alt.StrokeDash('Loại:N'), tooltip=['ym:T', 'Loại:N', alt.Tooltip('Giá trị:Q', format='.4f')])
    band = alt.Chart(ff).mark_area(opacity=0.16, color='#16c8f4').encode(x='date:T', y='lower:Q', y2='upper:Q')
    forecast_layers = [band, base_chart]

    selected_date = pd.DataFrame({'date': [pd.Timestamp(f'{month}-01')]})
    forecast_layers.append(alt.Chart(selected_date).mark_rule(color='#f1f8ff', strokeWidth=2, opacity=.8)
                          .encode(x='date:T'))
    st.altair_chart(chart_theme(alt.layer(*forecast_layers).properties(height=360)), width='stretch')
    st.caption('Dải cyan: khoảng tin cậy sai số; đường cyan nối liền mốc 08/2026 sang các tháng dự báo; vạch dọc sáng: tháng đang chọn.')

    # Bảng tổng hợp chi tiết 4 tháng dự báo
    section_title('Bảng tổng hợp 4 tháng dự báo (09–12/2026)', f'Giá trị dự báo, khí hậu đối sánh và khoảng tin cậy · {district}')
    fc_rows = []
    fc_badges = {}
    for r in ff.itertuples():
        m_str = r.date.strftime('%Y-%m')
        hz = int(r.horizon)
        f_val = float(r.forecast)
        c_val = float(r.climatology)
        diff = f_val - c_val
        st_cls, st_lbl, _ = evaluate_indicator_status(ind, f_val)
        fc_badges[st_lbl] = st_cls
        fc_rows.append({
            'Tháng': m_str,
            'Tầm dự báo': f'{hz} tháng',
            'Dự báo mô hình': f_val,
            'Khí hậu': c_val,
            'Chênh lệch': diff,
            'Khoảng tin cậy [Min — Max]': f'{r.lower:.{precision}f} — {r.upper:.{precision}f}',
            'Mức đánh giá': st_lbl
        })
    fc_table_df = pd.DataFrame(fc_rows)
    render_table(fc_table_df.round(4), badge_columns={'Mức đánh giá': fc_badges},
                 highlight_column='Tháng', highlight_value=month)

    section_title('Độ tin cậy dự báo', f'{name} · đánh giá tổng hợp toàn thành phố · áp dụng cùng cho khu vực đang xem: {district}')
    r = rel[rel.indicator == ind][['horizon', 'rmse_model', 'rmse_climatology']].copy()
    r['vs_climatology_pct'] = (r.rmse_model / r.rmse_climatology - 1) * 100
    r['reliability'] = [reliability_summary(model, climate)[1]
                        for model, climate in zip(r.rmse_model, r.rmse_climatology)]
    r['vs_climatology_pct'] = r['vs_climatology_pct'].round(2)
    r = r[['horizon', 'reliability', 'rmse_model', 'rmse_climatology', 'vs_climatology_pct']]
    r.columns = ['Dự báo trước (tháng)', 'Độ tin cậy', 'RMSE mô hình', 'RMSE khí hậu', 'So khí hậu (%)']
    reliability_badges = {'Độ tin cậy': {
        'Cải thiện so với khí hậu': 'status-low', 'Cải thiện nhẹ': 'status-low',
        'Tương đương khí hậu': 'status-mid', 'Kém hơn khí hậu': 'status-high',
        'Chưa đủ dữ liệu': 'status-mid'}}
    selected_horizon = int(fc.loc[(fc.indicator == ind) & (fc.date.dt.strftime('%Y-%m') == month), 'horizon'].iloc[0]) \
        if mode.startswith('Dự báo') else None
    render_table(r.round(4), badge_columns=reliability_badges,
                 highlight_column='Dự báo trước (tháng)' if selected_horizon is not None else None,
                 highlight_value=selected_horizon)
    st.caption('Bảng RMSE là kết quả đánh giá gộp toàn thành phố. '
               'Số âm ở cột "So khí hậu (%)" nghĩa là mô hình có sai số thấp hơn đường cơ sở khí hậu.')

    # Nhận định đa chỉ số thông minh
    fc_notes = generate_forecast_notes(ind, district, month, ff)
    notes_html = ''.join(f'<div class="callout warning"><strong>Nhận định {ind} ({month}).</strong> {html.escape(n)}</div>' for n in fc_notes)
    st.markdown(notes_html, unsafe_allow_html=True)
    st.markdown('<div class="callout"><strong>Cách diễn giải.</strong> Với phần lớn chỉ số, dự báo gần với khí hậu '
                'theo tháng. Mô hình thể hiện tốt hơn khác biệt không gian giữa các khu vực (NDVI, UTFVI) so với biến động chung '
                'của toàn thành phố.</div>', unsafe_allow_html=True)

# ---------------- TAB 4: KIỂM ĐỊNH 2026 ----------------
with tab_val:
    section_title(f'Kiểm định 2026 · {name}',
                  f'Tháng 1–8/2026 · So sánh thực tế quan trắc, mô hình và khí hậu · {district}')
    t = scope(ts[ts.indicator == ind])
    g = t.groupby('date')[['actual', 'forecast', 'climatology']].mean().reset_index()
    lg = g.melt('date', var_name='Loại', value_name='Giá trị')
    lg['Loại'] = lg['Loại'].map({'actual': 'Thực tế', 'forecast': 'Mô hình', 'climatology': 'Khí hậu'})
    ch = alt.Chart(lg).mark_line(point=True).encode(
        x=alt.X('date:T', title='Tháng'), y=alt.Y('Giá trị:Q', title=f'{name}{unit_txt}', scale=alt.Scale(zero=False)),
        color=alt.Color('Loại:N', scale=alt.Scale(domain=['Thực tế', 'Mô hình', 'Khí hậu'],
                                                   range=['#ff7393', '#16c8f4', '#ffb648'])),
        tooltip=['date:T', 'Loại:N', alt.Tooltip('Giá trị:Q', format='.4f')])
    if pd.Timestamp(f'{month}-01') in set(t.date.unique()):
        selected_test_date = pd.DataFrame({'date': [pd.Timestamp(f'{month}-01')]})
        ch = alt.layer(ch, alt.Chart(selected_test_date).mark_rule(
            color='#f1f8ff', strokeWidth=2, opacity=.8).encode(x='date:T'))
    st.altair_chart(chart_theme(ch.properties(height=340)), width='stretch')
    st.caption(f'Kiểm định cố định trên 8 tháng đầu năm 2026; dùng {len(t):,} cặp ô–tháng cho chỉ số/khu vực đang chọn. '
               'Đường dọc sáng đánh dấu tháng đã chọn nếu tháng đó thuộc giai đoạn kiểm định (01–08/2026).')

    # Chỉ số sai số tổng thể
    rmse_m = float(np.sqrt(((t.actual - t.forecast) ** 2).mean()))
    rmse_c = float(np.sqrt(((t.actual - t.climatology) ** 2).mean()))
    mae_m = float((t.actual - t.forecast).abs().mean())
    mae_c = float((t.actual - t.climatology).abs().mean())
    skill_pct, skill_lbl = reliability_summary(rmse_m, rmse_c)

    v1, v2, v3 = st.columns(3)
    v1.metric('RMSE Mô hình (theo ô)', f'{rmse_m:.4f}',
              delta=f'{skill_pct:+.2f}% so với khí hậu', delta_color='inverse')
    mae_delta = ((mae_m / mae_c - 1) * 100) if mae_c > 0 else np.nan
    v2.metric('MAE Mô hình (theo ô)', f'{mae_m:.4f}',
              delta=(f'{mae_delta:+.2f}% so với khí hậu' if pd.notna(mae_delta) else None), delta_color='inverse')
    v3.metric('Đánh giá độ chuẩn xác', skill_lbl,
              help='So sánh sai số kiểm thử với đường cơ sở khí hậu tham chiếu')

    # Bảng chi tiết từng tháng kiểm thử
    section_title('Chi tiết kiểm định từng tháng (1–8/2026)', f'Đánh giá sai số thực tế vs mô hình vs khí hậu theo từng tháng · {district}')
    monthly_records = []
    val_badges = {}
    for m_str, m_df in t.groupby(t.date.dt.strftime('%Y-%m')):
        m_act = float(m_df.actual.mean())
        m_fc = float(m_df.forecast.mean())
        m_cl = float(m_df.climatology.mean())
        m_rm = float(np.sqrt(((m_df.actual - m_df.forecast)**2).mean()))
        m_rc = float(np.sqrt(((m_df.actual - m_df.climatology)**2).mean()))
        m_delta_pct, m_lbl = reliability_summary(m_rm, m_rc)
        val_badges[m_lbl] = reliability_badges['Độ tin cậy'].get(m_lbl, 'status-mid')
        monthly_records.append({
            'Tháng': m_str,
            'Thực tế': m_act,
            'Dự báo mô hình': m_fc,
            'Khí hậu': m_cl,
            'RMSE mô hình': m_rm,
            'RMSE khí hậu': m_rc,
            'So khí hậu (%)': m_delta_pct,
            'Độ tin cậy': m_lbl,
            'Số ô': len(m_df)
        })
    monthly_val_df = pd.DataFrame(monthly_records)
    render_table(monthly_val_df.round(4), badge_columns={'Độ tin cậy': val_badges},
                 highlight_column='Tháng', highlight_value=month)
    if ind in LANDSAT:
        st.caption('Chỉ tính các ô-tháng có quan sát Landsat sạch mây thật.')

# ---------------- TAB 5: GIỚI THIỆU ----------------
with tab_about:
    section_title('Dữ liệu & phương pháp', 'Nguồn dữ liệu, quy trình dự báo và cách đánh giá')
    st.markdown(
        '<div class="info-grid">'
        '<div class="info-card"><div class="eyebrow">01 · Nguồn dữ liệu</div><strong>Quan trắc vệ tinh & khí hậu</strong>'
        '<p>Landsat 8/9, Sentinel-5P, MODIS MAIAC và ERA5-Land; xử lý trên Google Earth Engine, tổng hợp theo tháng trên lưới 1 km.</p></div>'
        '<div class="info-card"><div class="eyebrow">02 · Mô hình</div><strong>Dự báo theo khu vực</strong>'
        '<p>XGBoost ước lượng phần sai lệch so với khí hậu theo tháng cho từng ô lưới, với tầm dự báo từ 1 đến 4 tháng.</p></div>'
        '<div class="info-card"><div class="eyebrow">03 · Đánh giá</div><strong>Kiểm thử nhiều giai đoạn</strong>'
        '<p>Đối chiếu trên các giai đoạn 2023, 2024, 2025 và tháng 1–8/2026 với đường cơ sở khí hậu theo tháng.</p></div>'
        '</div>', unsafe_allow_html=True)
    section_title('Phân cấp UTFVI', 'Các ngưỡng diễn giải chỉ số sinh thái nhiệt')
    th = meta['utfvi_thresholds']
    ranges = [f'≤ {th[0]}'] + [f'{th[i]} - {th[i + 1]}' for i in range(len(th) - 1)] + [f'> {th[-1]}']
    utfvi_table = pd.DataFrame({'Mức': CLASS_NAMES, 'Khoảng UTFVI': ranges})
    render_table(utfvi_table)
    section_title('Hạn chế & lưu ý', 'Đọc kỹ trước khi so sánh hoặc diễn giải kết quả')
    notes_html = ''.join(f'<div class="note-item">{html.escape(note)}</div>' for note in meta['notes'])
    missing_months = ', '.join(meta['months_without_landsat'])
    notes_html += ('<div class="note-item">Các tháng không có ảnh Landsat đáng tin cậy: '
                   f'{html.escape(missing_months)}.</div>')
    st.markdown(f'<div class="note-list">{notes_html}</div>', unsafe_allow_html=True)
