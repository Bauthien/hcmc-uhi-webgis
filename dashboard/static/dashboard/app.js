// app.js - giao diện WebGIS (theo bố cục bản Streamlit cũ): Leaflet + Chart.js, dữ liệu lấy từ API Django.
// Hình học ô lưới tải một lần; giá trị theo ô tải lại mỗi khi đổi bộ lọc.
(function () {
  'use strict';

  const PALETTES = {
    YlOrRd: ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026'],
    YlGn: ['#ffffe5', '#f7fcb9', '#d9f0a3', '#addd8e', '#78c679', '#41ab5d', '#238443', '#006837', '#004529'],
    YlOrBr: ['#ffffe5', '#fff7bc', '#fee391', '#fec44f', '#fe9929', '#ec7014', '#cc4c02', '#993404', '#662506'],
    PuRd: ['#f7f4f9', '#e7e1ef', '#d4b9da', '#c994c7', '#df65b0', '#e7298a', '#ce1256', '#980043', '#67001f'],
    BuPu: ['#f7fcfd', '#e0ecf4', '#bfd3e6', '#9ebcda', '#8c96c6', '#8c6bb1', '#88419d', '#810f7c', '#4d004b'],
    Blues: ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'],
    diff: ['#053061', '#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7', '#fddbc7', '#f4a582', '#d6604d', '#b2182b', '#67001f'],
  };
  const IND_PALETTE = { UTFVI: 'YlOrRd', LST: 'YlOrRd', NDVI: 'YlGn', TVDI: 'YlOrBr', NO2: 'PuRd', CO: 'PuRd', AOD: 'BuPu', T2M: 'YlOrRd', PRECIP: 'Blues' };
  const CLASS_COLORS = ['#1a9850', '#a6d96a', '#fee08b', '#fdae61', '#f46d43', '#a50026'];
  const LEVEL_SEMANTICS = {
    LST: ['Mát mẻ', 'Nóng gắt'], NDVI: ['Thảm xanh thưa', 'Xanh tươi dồi dào'], TVDI: ['Ẩm', 'Khô hạn'],
    NO2: ['Thấp', 'Cao'], CO: ['Thấp', 'Cao'], AOD: ['Quang đãng', 'Mù sol khí dày'], UTFVI: ['Sinh thái tốt', 'Đảo nhiệt gay gắt'],
    T2M: ['Mát', 'Nóng'], PRECIP: ['Ít mưa', 'Mưa nhiều'],
  };
  const C = { cyan: '#16c8f4', hist: '#7c9bb8', clim: '#ffb648', actual: '#ff7393', city: '#7c9bb8', grid: '#1b3047', text: '#91a4ba' };
  const YEAR_COLORS = ['#7c9bb8', '#a78bfa', '#42d9a4', '#ffb648', '#ff7393', '#4dabf7', '#16c8f4'];
  const ALL = 'Toàn thành phố';

  const S = { ind: 'LST', district: null, mode: 'history', month: null, view: 'forecast', observedOnly: false, scale: 'auto', tab: 'map' };
  let META = null, IND = {}, DIST = {}, CELL = {}, V = null, PREV = null, lastRange = null;
  let map = null, cellLayer = null, distLayer = null, legend = null;
  const charts = {}, cache = {};

  // ---------------- tiện ích ----------------
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  async function getJSON(url) {
    if (cache[url]) return cache[url];
    const r = await fetch(url);
    const body = await r.json();
    if (!r.ok) throw new Error(body.error || r.statusText);
    cache[url] = body;
    return body;
  }
  const prec = (ind) => ({ LST: 1, NO2: 1, CO: 1, UTFVI: 4, T2M: 1, PRECIP: 0 }[ind] ?? 3);
  const WEATHER = ['T2M', 'PRECIP'];
  function fmt(v, d) {
    if (v === null || v === undefined || Number.isNaN(v)) return '—';
    return Number(v).toLocaleString('vi-VN', { minimumFractionDigits: d, maximumFractionDigits: d });
  }
  const tiny = (v, d) => Math.abs(v) < 0.5 * 10 ** -d;          // làm tròn thành 0 ở d chữ số
  const sgn = (v, d) => (tiny(v, d) ? fmt(0, d) : (v > 0 ? '+' : '') + fmt(v, d));
  const unitSfx = () => (IND[S.ind].unit ? ' ' + IND[S.ind].unit : '');
  const qs = (p) => Object.entries(p).filter(([, v]) => v !== null && v !== undefined).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&');
  const mean = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN);
  function quantile(sorted, q) {
    if (!sorted.length) return NaN;
    const p = (sorted.length - 1) * q, i = Math.floor(p);
    return sorted[i] + (sorted[Math.min(i + 1, sorted.length - 1)] - sorted[i]) * (p - i);
  }
  function hexToRgb(h) { const n = parseInt(h.slice(1), 16); return [n >> 16, (n >> 8) & 255, n & 255]; }
  function ramp(name, t) {
    const p = PALETTES[name];
    t = Math.min(1, Math.max(0, t)) * (p.length - 1);
    const i = Math.min(p.length - 2, Math.floor(t)), f = t - i;
    const a = hexToRgb(p[i]), b = hexToRgb(p[i + 1]);
    return `rgb(${a.map((x, k) => Math.round(x + (b[k] - x) * f)).join(',')})`;
  }
  const districtName = () => (S.district === null ? ALL : DIST[S.district].name);
  const districtParam = () => (S.district === null ? 'all' : S.district);
  const classNames = () => META.meta.utfvi_class_names || [];
  const inScope = (cellId) => S.district === null || CELL[cellId].district_id === S.district;
  const isDiff = () => S.mode === 'forecast' && S.view === 'diff';
  const viewText = () => ({ forecast: 'Dự báo', climatology: 'Khí hậu theo tháng', diff: 'Chênh (dự báo - khí hậu)' }[S.view]);

  function table(cols, rows, opts = {}) {
    const head = cols.map((c) => `<th>${esc(c.label)}</th>`).join('');
    const body = rows.map((r) => {
      const sel = opts.selected && opts.selected(r) ? ' is-selected' : '';
      const click = opts.rowId ? ` class="click${sel}" data-id="${opts.rowId(r)}"` : (sel ? ` class="${sel.trim()}"` : '');
      return `<tr${click}>` + cols.map((c) => `<td${c.num ? ' class="num"' : ''}>${c.html ? c.html(r) : esc(c.get(r))}</td>`).join('') + '</tr>';
    }).join('');
    return `<div class="table-shell"><table class="dark-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  }
  const pill = (cls, text) => `<span class="status-pill ${cls}">${esc(text)}</span>`;

  // Nhãn độ tin cậy theo quy tắc của bảng reliability (Cell 24): chỉ NDVI, UTFVI, AOD được coi là "Cải thiện"
  function relLabel(ind, pct) {
    if (pct === null || pct === undefined || Number.isNaN(pct)) return 'Chưa đủ dữ liệu';
    const can = ['NDVI', 'UTFVI', 'AOD'].includes(ind);
    if (can && pct <= -5) return 'Cải thiện so với khí hậu';
    if (can && pct <= -2) return 'Cải thiện nhẹ';
    if (pct > 3) return 'Kém hơn khí hậu';
    return 'Tương đương khí hậu';
  }
  const REL_CLS = { 'Cải thiện so với khí hậu': 'status-low', 'Cải thiện nhẹ': 'status-low', 'Tương đương khí hậu': 'status-mid', 'Kém hơn khí hậu': 'status-high', 'Chưa đủ dữ liệu': 'status-mid' };

  // Phân loại hiển thị (ngưỡng tự đặt để đọc nhanh, không phải tiêu chuẩn môi trường)
  function evalStatus(ind, v) {
    if (v === null || Number.isNaN(v)) return ['status-mid', 'Chưa có dữ liệu', 'Chưa đủ dữ liệu cho thời điểm và khu vực này.'];
    const d = prec(ind), x = fmt(v, d);
    const T = {
      LST: [[30, 'status-low', 'Nhiệt độ mát mẻ'], [35, 'status-low', 'Nhiệt độ bình thường'], [38, 'status-mid', 'Nhiệt độ khá cao'], [Infinity, 'status-high', 'Nhiệt độ rất cao']],
      TVDI: [[0.4, 'status-low', 'Độ ẩm dồi dào'], [0.6, 'status-mid', 'Khô hạn nhẹ'], [0.75, 'status-high', 'Khô hạn vừa'], [Infinity, 'status-high', 'Khô hạn nghiêm trọng']],
      NO2: [[35, 'status-low', 'NO₂ thấp'], [55, 'status-mid', 'NO₂ trung bình'], [75, 'status-mid', 'NO₂ khá cao'], [Infinity, 'status-high', 'NO₂ cao']],
      CO: [[30, 'status-low', 'CO thấp'], [38, 'status-mid', 'CO trung bình'], [Infinity, 'status-high', 'CO cao']],
      AOD: [[0.2, 'status-low', 'AOD thấp · Trời trong'], [0.3, 'status-mid', 'AOD trung bình'], [0.4, 'status-high', 'AOD khá cao'], [Infinity, 'status-high', 'AOD cao']],
    };
    const DESC = {
      LST: `Nhiệt độ bề mặt trung bình đạt ${x} °C (ảnh Landsat chụp khoảng 10 giờ sáng; nhiệt độ bề mặt cao hơn nhiệt độ không khí).`,
      TVDI: `Chỉ số hạn khô ${x}: càng gần 1 bề mặt càng khô, càng gần 0 càng ẩm.`,
      NO2: `Cột NO₂ tầng đối lưu trung bình ${x} µmol/m² (Sentinel-5P), là lượng trong cả cột khí quyển, không phải nồng độ mặt đất.`,
      CO: `Cột CO trung bình ${x} mmol/m² (Sentinel-5P), là lượng trong cả cột khí quyển, không phải nồng độ mặt đất.`,
      AOD: `Độ dày quang học sol khí ${x} (MODIS MAIAC), phản ánh lượng hạt lơ lửng trong cột khí quyển.`,
    };
    // Thời tiết ERA5-Land: không đặt ngưỡng đánh giá, chỉ mô tả
    if (ind === 'T2M') return ['status-neutral', `Nhiệt độ không khí ${x} °C`, `Nhiệt độ không khí trung bình tháng ở độ cao 2 m đạt ${x} °C (ERA5-Land, ô gốc khoảng 9 km nên ít khác biệt giữa các quận).`];
    if (ind === 'PRECIP') return ['status-neutral', `Lượng mưa ${x} mm`, `Tổng lượng mưa tháng ${x} mm (ERA5-Land, ô gốc khoảng 9 km).`];
    if (ind === 'UTFVI') {
      const k = classifyUtfvi(v), n = classNames()[k - 1];
      const cls = k <= 2 ? 'status-low' : k === 3 ? 'status-mid' : 'status-high';
      const lab = k <= 2 ? 'Sinh thái tốt' : k === 3 ? 'Sinh thái trung bình' : k <= 5 ? 'Cảnh báo nhiệt' : 'Báo động nhiệt';
      return [cls, `${lab} (${n})`, `UTFVI trung bình ${x}, mức "${n}". UTFVI so sánh LST của ô với LST trung bình toàn thành phố cùng tháng.`];
    }
    if (ind === 'NDVI') {
      if (v >= 0.45) return ['status-low', `Thảm xanh dồi dào (${x})`, `Độ phủ thực vật cao (NDVI ${x}).`];
      if (v >= 0.3) return ['status-mid', `Thảm xanh trung bình (${x})`, `Độ phủ thực vật trung bình (NDVI ${x}), xen kẽ mảng xanh và công trình.`];
      return ['status-high', `Thảm xanh thấp (${x})`, `Độ phủ thực vật thấp (NDVI ${x}); giá trị gần 0 hoặc âm thường là mặt nước hoặc bề mặt xây dựng.`];
    }
    const hit = T[ind].find((t) => v <= t[0]);
    return [hit[1], `${hit[2]} (${x}${ind === 'LST' ? ' °C' : ''})`, DESC[ind]];
  }
  function classifyUtfvi(v) {
    let k = 1;
    (META.meta.utfvi_thresholds || []).forEach((t) => { if (v > t) k += 1; });
    return k;
  }
  function sensorInfo() {
    const ind = S.ind, hist = S.mode === 'history';
    if (IND[ind].landsat) {
      const bad = META.meta.months_without_landsat.includes(S.month);
      if (!hist) return ['Landsat 8/9 (TIRS & OLI)', 'Mô hình XGBoost dự báo', 'status-cyan'];
      return bad ? ['Landsat 8/9 (TIRS & OLI)', 'Nội suy (không có ảnh sạch mây)', 'status-mid'] : ['Landsat 8/9 (TIRS & OLI)', 'Ảnh quan sát thật (1 km)', 'status-low'];
    }
    const sensor = ind === 'AOD' ? 'MODIS (MAIAC 1 km)' : WEATHER.includes(ind) ? 'ERA5-Land (tái phân tích, ~9 km)' : 'Sentinel-5P (TROPOMI)';
    const histText = WEATHER.includes(ind) ? 'Trung bình tháng (tái phân tích)' : 'Trung bình tháng từ vệ tinh';
    return hist ? [sensor, histText, 'status-low'] : [sensor, 'Mô hình XGBoost dự báo', 'status-cyan'];
  }

  // ---------------- khởi tạo ----------------
  async function init() {
    Chart.defaults.color = C.text;
    Chart.defaults.borderColor = C.grid;
    Chart.defaults.font.family = "'Be Vietnam Pro', 'Segoe UI', sans-serif";

    META = await getJSON('/api/meta/');
    META.indicators.forEach((i) => { IND[i.id] = i; });
    META.districts.forEach((d) => { DIST[d.id] = d; });
    // Mở sẵn theo địa chỉ, ví dụ /?indicator=T2M&mode=forecast&district=4#forecast
    const qp = new URLSearchParams(location.search);
    if (IND[qp.get('indicator')]) S.ind = qp.get('indicator');
    if (qp.get('mode') === 'forecast') {
      S.mode = 'forecast';
      document.querySelector('input[name=mode][value=forecast]').checked = true;
    }
    if (DIST[qp.get('district')]) S.district = Number(qp.get('district'));
    $('sel-indicator').innerHTML = META.indicators.map((i) => `<option value="${i.id}"${i.id === S.ind ? ' selected' : ''}>${esc(i.name)}</option>`).join('');
    $('sel-district').innerHTML += META.districts.map((d) => `<option value="${d.id}">${esc(d.name)}</option>`).join('');
    if (S.district !== null) $('sel-district').value = String(S.district);
    S.month = META.history_months[META.history_months.length - 1];
    setupMonths();
    bindEvents();
    const tab = location.hash.slice(1);
    if (document.querySelector(`.tab[data-tab="${tab}"]`)) showTab(tab);
    initMap();
    renderAbout();

    const [cells, dists] = await Promise.all([getJSON('/api/cells/'), getJSON('/api/districts/')]);
    cells.features.forEach((f) => {
      const ring = f.geometry.coordinates[0];
      const xs = ring.map((p) => p[0]), ys = ring.map((p) => p[1]);
      CELL[f.properties.cell_id] = { ...f.properties, lon: (Math.min(...xs) + Math.max(...xs)) / 2, lat: (Math.min(...ys) + Math.max(...ys)) / 2 };
    });
    drawGeometry(cells, dists);
    refresh();
  }

  function monthList() {
    return S.mode === 'history' ? META.history_months : META.forecast_months.map((f) => f.month);
  }
  function setupMonths() {
    const months = monthList();
    if (!months.includes(S.month)) S.month = S.mode === 'history' ? months[months.length - 1] : months[Math.min(1, months.length - 1)];
    const r = $('rng-month');
    r.max = months.length - 1;
    r.value = months.indexOf(S.month);
    $('lbl-month').textContent = S.mode === 'history' ? 'Tháng' : 'Tháng dự báo';
    $('month-value').textContent = S.month;
  }

  function bindEvents() {
    document.querySelectorAll('.tab').forEach((b) => b.addEventListener('click', () => {
      history.replaceState(null, '', '#' + b.dataset.tab);
      showTab(b.dataset.tab);
      refresh();
    }));
    document.querySelectorAll('input[name=mode]').forEach((r) => r.addEventListener('change', () => { S.mode = r.value; setupMonths(); refresh(); }));
    document.querySelectorAll('input[name=view]').forEach((r) => r.addEventListener('change', () => { S.view = r.value; refresh(); }));
    document.querySelectorAll('input[name=scale]').forEach((r) => r.addEventListener('change', () => { S.scale = r.value; refresh(); }));
    $('sel-indicator').addEventListener('change', (e) => { S.ind = e.target.value; refresh(); });
    $('sel-district').addEventListener('change', (e) => selectDistrict(e.target.value === 'all' ? null : Number(e.target.value)));
    $('rng-month').addEventListener('input', (e) => { S.month = monthList()[Number(e.target.value)]; $('month-value').textContent = S.month; });
    $('rng-month').addEventListener('change', () => refresh());
    $('chk-observed').addEventListener('change', (e) => { S.observedOnly = e.target.checked; refresh(); });
    $('btn-csv').addEventListener('click', exportCsv);
    $('menu-btn').addEventListener('click', () => $('sidebar').classList.toggle('open'));
  }

  function showTab(tab) {
    S.tab = tab;
    document.querySelectorAll('.tab').forEach((x) => x.classList.toggle('active', x.dataset.tab === tab));
    document.querySelectorAll('.panel').forEach((p) => p.classList.toggle('active', p.id === 'tab-' + tab));
    if (tab === 'map' && map) { map.invalidateSize(); fitOnce(); }
  }

  function selectDistrict(id) {
    S.district = id;
    $('sel-district').value = id === null ? 'all' : String(id);
    if (S.tab === 'map') zoomToScope();
    refresh();
  }

  function syncSidebar() {
    const landsat = IND[S.ind].landsat, hist = S.mode === 'history';
    $('wrap-view').hidden = hist;
    $('wrap-observed').hidden = !hist;
    $('chk-observed').disabled = !landsat;
    $('wrap-scale').querySelectorAll('input').forEach((i) => { i.disabled = isDiff() || (S.ind === 'UTFVI' && !isDiff()); });
    $('side-warning').hidden = !(hist && landsat && META.meta.months_without_landsat.includes(S.month));
  }

  async function refresh() {
    syncSidebar();
    try {
      await loadValues();
      renderHeader();
      const jobs = { map: renderMap, history: refreshHistory, forecast: refreshForecast, validation: refreshValidation };
      if (jobs[S.tab]) await jobs[S.tab]();
    } catch (e) {
      console.error(e);
      const m = $('map-msg');
      m.textContent = 'Lỗi tải dữ liệu: ' + e.message;
      m.hidden = false;
    }
  }

  function valuesUrl(month) {
    const p = { mode: S.mode, indicator: S.ind, month };
    if (S.mode === 'forecast') p.view = S.view;
    if (S.mode === 'history' && S.observedOnly && IND[S.ind].landsat) p.observed_only = 1;
    return '/api/values/?' + qs(p);
  }
  async function loadValues() {
    V = await getJSON(valuesUrl(S.month));
    PREV = null;
    if (S.mode === 'forecast' && S.view === 'forecast') {
      await getJSON(valuesUrl(S.month).replace('view=forecast', 'view=climatology'));   // để so với khí hậu
    }
    if (S.mode === 'history') {
      const i = META.history_months.indexOf(S.month);
      if (i > 0) PREV = await getJSON(valuesUrl(META.history_months[i - 1]));
    }
  }
  const scoped = (vals) => Object.entries(vals.values).filter(([c]) => inScope(c)).map(([, v]) => v);

  // ---------------- tiêu đề và khung nhận định ----------------
  function renderHeader() {
    const ind = IND[S.ind], d = prec(S.ind), u = unitSfx();
    const name = ind.name.endsWith(`(${S.ind})`) ? `${esc(ind.name.slice(0, -(S.ind.length + 2)))}<span>(${S.ind})</span>` : esc(ind.name);
    $('hero-title').innerHTML = name;
    const modeText = S.mode === 'history' ? 'Dữ liệu lịch sử 2020–2026' : `Dự báo mô hình (${viewText()})`;
    $('hero-subtitle').innerHTML = `${S.month} &nbsp;·&nbsp; ${esc(districtName())} &nbsp;·&nbsp; ${modeText}`;

    const avg = mean(scoped(V));
    let st;
    if (isDiff()) {
      st = Number.isNaN(avg) ? ['status-cyan', 'Chưa có dữ liệu', 'Chưa đủ dữ liệu để tính chênh lệch.']
        : ['status-cyan', `${avg > 0 ? 'Cao hơn' : avg < 0 ? 'Thấp hơn' : 'Bằng'} khí hậu (${sgn(avg, d)}${u})`,
          'Giá trị đang xem là chênh lệch dự báo trừ khí hậu; số dương nghĩa là cao hơn mức khí hậu tham chiếu, không phải giá trị tuyệt đối của chỉ số.'];
    } else st = evalStatus(S.ind, avg);

    let delta = '';
    if (S.mode === 'forecast' && S.view === 'forecast') {
      const clim = cache[valuesUrl(S.month).replace('view=forecast', 'view=climatology')];
      if (clim) {
        const dc = avg - mean(scoped(clim));
        delta = `<span class="hero-tag">Chênh lệch khí hậu: <strong>${sgn(dc, d)}${u}</strong> (${tiny(dc, d) ? 'xấp xỉ' : dc > 0 ? 'cao hơn' : 'thấp hơn'})</span>`;
      }
    } else if (PREV) {
      const dm = avg - mean(scoped(PREV));
      if (!Number.isNaN(dm)) delta = `<span class="hero-tag">So tháng trước (${PREV.month}): <strong>${sgn(dm, d)}${u}</strong> (${tiny(dm, d) ? 'không đổi' : dm > 0 ? 'tăng' : 'giảm'})</span>`;
    }
    $('hero-tags').innerHTML = pill(st[0], st[1]) + `<span class="hero-tag">Trung bình: <strong>${fmt(avg, d)}${u}</strong></span>` + delta;

    const [sensor, quality, qcls] = sensorInfo();
    $('insight').innerHTML = `<div class="insight-header">${pill(st[0], st[1])}${pill('status-cyan', 'Nguồn: ' + sensor)}${pill(qcls, quality)}</div>
      <strong>${S.mode === 'history' ? 'Hiện trạng' : 'Dự báo'} ${esc(ind.name)} tại ${esc(districtName())} (Tháng ${S.month})</strong><p>${esc(st[2])}</p>`;
  }

  // ---------------- bản đồ ----------------
  function initMap() {
    map = L.map('map', { preferCanvas: true, zoomSnap: 0.25 }).setView([10.78, 106.7], 10);
    // Nền OSM được đảo màu thành tối bằng CSS (lớp osm-dark); CARTO tối là nền dự phòng, không cần đảo màu
    const osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18, className: 'osm-dark', referrerPolicy: 'strict-origin-when-cross-origin',
      attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
    const carto = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19, subdomains: 'abcd', attribution: '&copy; OpenStreetMap contributors &copy; CARTO' });
    map._bases = { 'OpenStreetMap (tối)': osm, 'CARTO tối (dự phòng)': carto };
    L.control.scale({ position: 'bottomleft' }).addTo(map);
    const locate = L.control({ position: 'topleft' });
    locate.onAdd = () => {
      const b = L.DomUtil.create('button', 'map-locate-control');
      b.type = 'button';
      b.innerHTML = '<span aria-hidden="true">⌖</span><span>Tới khu vực</span>';
      L.DomEvent.disableClickPropagation(b);
      L.DomEvent.on(b, 'click', zoomToScope);
      return b;
    };
    locate.addTo(map);
    legend = L.control({ position: 'topright' });
    legend.onAdd = () => L.DomUtil.create('div', 'map-legend');
    legend.addTo(map);
  }

  function drawGeometry(cells, dists) {
    cellLayer = L.geoJSON(cells, {
      style: () => ({ stroke: false, fillOpacity: 0 }),
      onEachFeature: (f, layer) => {
        layer.on('click', () => selectDistrict(f.properties.district_id));
        layer.bindTooltip(() => cellTooltip(f.properties), { sticky: true });
      },
    }).addTo(map);
    distLayer = L.geoJSON(dists, { interactive: false, style: () => ({ color: '#9fb3c8', weight: 0.6, fill: false, opacity: 0.45 }) }).addTo(map);
    L.control.layers(map._bases, { 'Giá trị theo ô (1 km)': cellLayer, 'Ranh giới quận/huyện': distLayer }, { position: 'bottomright' }).addTo(map);
    fitOnce();
  }

  let fitted = false;
  function fitOnce() {
    if (fitted || !distLayer || S.tab !== 'map') return;
    zoomToScope();
    fitted = true;
  }
  function zoomToScope() {
    if (!distLayer) return;
    let b = distLayer.getBounds();
    if (S.district !== null) distLayer.eachLayer((l) => { if (l.feature.properties.district_id === S.district) b = l.getBounds(); });
    map.fitBounds(b, { padding: [28, 28], maxZoom: S.district === null ? 10.5 : 12 });
  }

  function cellTooltip(p) {
    if (!V) return esc(p.district);
    const v = V.values[p.cell_id];
    let txt = v === undefined ? 'không có giá trị' : (isDiff() ? sgn(v, prec(S.ind)) : fmt(v, prec(S.ind))) + unitSfx();
    const k = V.classes && V.classes[p.cell_id];
    if (k) txt = `${classNames()[k - 1]} (UTFVI ${fmt(v, 4)})`;
    return `<b>${esc(p.district)}</b> — ${txt}`;
  }

  function colorRange() {
    const vals = scoped(V).sort((a, b) => a - b);
    if (isDiff()) {
      const abs = vals.map(Math.abs).sort((a, b) => a - b);
      const mx = Math.max(quantile(abs, 0.99) || 0, 1e-6);
      return { lo: -mx, hi: mx, label: 'Chênh lệch khí hậu' };
    }
    if (S.scale === 'fixed' || !vals.length) return { lo: V.range[0], hi: V.range[1], label: 'Chuẩn 2020–2026' };
    let lo = quantile(vals, 0.01), hi = quantile(vals, 0.99);
    if (lo >= hi) { lo = vals[0]; hi = vals[vals.length - 1]; }
    if (lo >= hi) { const p = Math.max(Math.abs(lo) * 0.01, 1e-4); lo -= p; hi += p; }
    return { lo, hi, label: `Động tháng ${S.month}` };
  }

  async function renderMap() {
    const useClasses = !!V.classes;
    const rg = useClasses ? null : colorRange();
    lastRange = rg;
    const pal = isDiff() ? 'diff' : IND_PALETTE[S.ind];
    if (cellLayer) {
      cellLayer.setStyle((f) => {
        const id = f.properties.cell_id, v = V.values[id];
        if (v === undefined) return { stroke: false, fillOpacity: 0 };
        const col = useClasses ? CLASS_COLORS[(V.classes[id] || 1) - 1] : ramp(pal, (v - rg.lo) / (rg.hi - rg.lo));
        return { stroke: false, fillColor: col, fillOpacity: inScope(id) ? 0.85 : 0.15 };
      });
    }
    if (distLayer) {
      distLayer.setStyle((f) => (f.properties.district_id === S.district
        ? { color: C.cyan, weight: 2.4, fill: false, opacity: 1 }
        : { color: '#9fb3c8', weight: 0.6, fill: false, opacity: 0.45 }));
    }
    const msg = $('map-msg');
    if (V.landsat_missing) {
      msg.textContent = V.n_cells === 0
        ? `Tháng ${S.month} không có ảnh Landsat đủ sạch mây. Bỏ chọn "Chỉ hiển thị ô có ảnh Landsat quan sát thật" để xem giá trị nội suy.`
        : `Tháng ${S.month} không có ảnh Landsat đủ sạch mây: giá trị đang hiển thị là nội suy.`;
      msg.hidden = false;
    } else msg.hidden = true;

    const info = $('map-info');
    if (S.mode === 'forecast' && V.reliability) {
      const r = V.reliability, valueDesc = { forecast: 'Dự báo mô hình', climatology: 'Khí hậu tham chiếu', diff: 'Chênh lệch dự báo − khí hậu' }[S.view];
      info.innerHTML = `Đang xem <strong>${valueDesc} · ${esc(IND[S.ind].name)} · ${S.month} · ${esc(districtName())}</strong>. Tầm dự báo: <strong>${V.horizon} tháng</strong>; độ tin cậy mô hình toàn thành phố tại tầm này: <strong>${esc(r.reliability)}</strong> (${sgn(r.vs_climatology_pct, 1)}% RMSE so với khí hậu; số âm nghĩa là tốt hơn).`;
      info.hidden = false;
    } else info.hidden = true;

    renderLegend(rg, pal);
    renderMetrics();
    renderRanking();
  }

  function renderLegend(rg, pal) {
    const el = legend.getContainer(), ind = IND[S.ind], d = prec(S.ind);
    const meta = (badge) => `<div class="map-legend-meta"><span>${S.month} · ${esc(districtName())}</span><span class="map-legend-badge">${esc(badge)}</span></div>`;
    if (V.classes) {
      const ks = Object.entries(V.classes).filter(([c]) => inScope(c)).map(([, k]) => k);
      const t = META.meta.utfvi_thresholds;
      const ranges = ['≤ 0', `0 – ${t[1]}`, `${t[1]} – ${t[2]}`, `${t[2]} – ${t[3]}`, `${t[3]} – ${t[4]}`, `> ${t[4]}`];
      el.innerHTML = `<div class="map-legend-title">Mức cảnh báo UTFVI</div>${meta('Phân cấp UTFVI')}<div class="map-legend-classes">` +
        classNames().map((n, i) => `<div class="map-legend-class"><div class="map-legend-class-left"><span class="map-legend-swatch" style="background:${CLASS_COLORS[i]}"></span><span>${esc(n)} <small>(${ranges[i]})</small></span></div>
          <span class="map-legend-pct">${fmt(ks.length ? ks.filter((k) => k === i + 1).length / ks.length * 100 : 0, 1)}%</span></div>`).join('') + '</div>';
      return;
    }
    const ticks = [0, 1, 2, 3, 4].map((i) => `<span>${fmt(rg.lo + (rg.hi - rg.lo) * i / 4, d)}</span>`).join('');
    const sem = LEVEL_SEMANTICS[S.ind];
    const labels = isDiff() ? '<span>◀ Thấp hơn khí hậu</span><span>Chuẩn (0)</span><span>Cao hơn khí hậu ▶</span>'
      : `<span>◀ Thấp (${sem[0]})</span><span>Trung bình</span><span>Cao (${sem[1]}) ▶</span>`;
    const title = (isDiff() ? 'Chênh ' : '') + ind.name + (ind.unit ? ` (${ind.unit})` : '');
    el.innerHTML = `<div class="map-legend-title">${esc(title)}</div>${meta(rg.label)}<div class="map-legend-ticks">${ticks}</div>
      <div class="map-legend-gradient" style="background:linear-gradient(90deg,${PALETTES[pal].join(',')})"></div>
      <div class="map-legend-labels">${labels}</div><div class="map-legend-unit">Đơn vị: ${esc(ind.unit || 'không thứ nguyên')}</div>`;
  }

  function alertMetric(vals, classes) {
    const share = (f) => (vals.length ? vals.filter(f).length / vals.length * 100 : 0);
    if (isDiff()) return ['Tỉ lệ ô cao hơn khí hậu', share((v) => v > 0), 'Tỉ lệ ô có chênh lệch dự báo − khí hậu dương.'];
    if (classes) return ['Tỉ lệ ô cảnh báo nhiệt', classes.length ? classes.filter((k) => k >= 4).length / classes.length * 100 : 0, 'Tỉ lệ ô ở mức UTFVI Mạnh, Rất mạnh hoặc Cực mạnh (mức 4–6).'];
    const cityMean = mean(Object.values(V.values));
    return {
      T2M: ['Tỉ lệ ô nóng hơn TB thành phố', share((v) => v > cityMean), 'Tỉ lệ ô có nhiệt độ không khí cao hơn trung bình toàn thành phố cùng tháng.'],
      PRECIP: ['Tỉ lệ ô mưa nhiều hơn TB thành phố', share((v) => v > cityMean), 'Tỉ lệ ô có lượng mưa cao hơn trung bình toàn thành phố cùng tháng.'],
      LST: ['Tỉ lệ ô nhiệt rất cao (>38°C)', share((v) => v > 38), 'Tỉ lệ ô có nhiệt độ bề mặt trên 38 °C.'],
      NDVI: ['Tỉ lệ ô thảm xanh thấp (<0.30)', share((v) => v < 0.3), 'Tỉ lệ ô có NDVI dưới 0,30.'],
      TVDI: ['Tỉ lệ ô hạn vừa – nặng', share((v) => v >= 0.6), 'Tỉ lệ ô có TVDI từ 0,60 trở lên.'],
      NO2: ['Tỉ lệ ô NO₂ cao (>75)', share((v) => v > 75), 'Tỉ lệ ô có cột NO₂ trên 75 µmol/m².'],
      CO: ['Tỉ lệ ô CO cao (>38)', share((v) => v > 38), 'Tỉ lệ ô có cột CO trên 38 mmol/m².'],
      AOD: ['Tỉ lệ ô sol khí cao (>0.30)', share((v) => v > 0.3), 'Tỉ lệ ô có AOD trên 0,30.'],
      UTFVI: ['Tỉ lệ ô UTFVI dương', share((v) => v > 0), 'Tỉ lệ ô nóng hơn trung bình toàn thành phố.'],
    }[S.ind];
  }

  function metricCard(label, value, delta, deltaCls, help) {
    return `<div class="metric"${help ? ` title="${esc(help)}"` : ''}><div class="metric-label">${esc(label)}${help ? ' ⓘ' : ''}</div>
      <div class="metric-value">${value}</div>${delta ? `<span class="metric-delta ${deltaCls}">${esc(delta)}</span>` : ''}</div>`;
  }

  function renderMetrics() {
    const d = prec(S.ind), u = unitSfx();
    const all = Object.values(V.values), vals = scoped(V);
    const classes = V.classes ? Object.entries(V.classes).filter(([c]) => inScope(c)).map(([, k]) => k) : null;
    const cityMean = mean(all), areaMean = mean(vals);
    const range = vals.length ? `${fmt(Math.min(...vals), d)} — ${fmt(Math.max(...vals), d)}${u}` : '—';
    const [aLabel, aVal, aHelp] = alertMetric(vals, classes);
    const f = (v) => (isDiff() ? sgn(v, d) : fmt(v, d));
    let html;
    if (S.district === null) {
      let delta = null;
      if (S.mode === 'forecast' && S.view === 'forecast') {
        const clim = cache[valuesUrl(S.month).replace('view=forecast', 'view=climatology')];
        if (clim) delta = `${sgn(cityMean - mean(Object.values(clim.values)), d)}${u} so với khí hậu`;
      } else if (PREV) delta = `${sgn(cityMean - mean(Object.values(PREV.values)), d)}${u} so với ${PREV.month}`;
      html = metricCard('Trung bình toàn TP', f(cityMean) + u, delta, delta && delta.startsWith('-') ? 'delta-down' : 'delta-up')
        + metricCard('Biên độ dao động (Min — Max)', range)
        + metricCard(aLabel, fmt(aVal, 1) + '%', null, '', aHelp)
        + metricCard('Số ô có dữ liệu', `${fmt(all.length, 0)} ô`, `${fmt(all.length / 1981 * 100, 0)}% lưới TP`, 'delta-off');
    } else {
      const diff = areaMean - cityMean;
      html = metricCard(`Trung bình ${districtName()}`, f(areaMean) + u, `${sgn(diff, d)}${u} so với toàn TP`, diff < 0 ? 'delta-down' : 'delta-up')
        + metricCard('Trung bình toàn thành phố', f(cityMean) + u)
        + metricCard(aLabel, fmt(aVal, 1) + '%', null, '', aHelp)
        + metricCard(`Biên độ ${districtName()}`, range, `${fmt(vals.length, 0)} ô (${fmt(vals.length / Math.max(all.length, 1) * 100, 1)}% TP)`, 'delta-off');
    }
    $('metrics').innerHTML = html;
  }

  function renderRanking() {
    const d = prec(S.ind), u = unitSfx();
    const acc = {};
    Object.entries(V.values).forEach(([c, v]) => {
      const id = CELL[c].district_id, a = acc[id] || (acc[id] = { sum: 0, n: 0, strong: 0, nk: 0 });
      a.sum += v; a.n += 1;
      const k = V.classes && V.classes[c];
      if (k) { a.nk += 1; a.strong += k >= 4 ? 1 : 0; }
    });
    const rows = Object.entries(acc).map(([id, a]) => ({ id: Number(id), name: DIST[id].name, mean: a.sum / a.n, n: a.n, strong: a.nk ? a.strong / a.nk * 100 : null }))
      .sort((a, b) => b.mean - a.mean);
    const levels = { NDVI: { 'Rất cao': 'status-low', 'Cao': 'status-low', 'Trung bình': 'status-mid', 'Thấp': 'status-high' } };
    const lvCls = isDiff() ? null : (levels[S.ind] || { 'Rất cao': 'status-high', 'Cao': 'status-high', 'Trung bình': 'status-mid', 'Thấp': 'status-low' });
    rows.forEach((r, i) => {
      r.rank = i + 1;
      const p = i / rows.length;
      r.level = p < 0.1 ? 'Rất cao' : p < 0.35 ? 'Cao' : p < 0.7 ? 'Trung bình' : 'Thấp';
    });
    const showCls = !!V.classes;
    const cols = [
      { label: 'Xếp hạng', html: (r) => `<span class="rank-number${r.rank <= 3 ? ' is-top' : ''}">${String(r.rank).padStart(2, '0')}</span>` },
      { label: 'Khu vực', get: (r) => r.name + (DIST[r.id].n_cells < 10 ? ' *' : '') },
      { label: (isDiff() ? 'Chênh ' : 'Chỉ số ') + S.ind, num: true, get: (r) => (isDiff() ? sgn(r.mean, d) : fmt(r.mean, d)) },
      { label: 'Số ô', get: (r) => r.n },
    ];
    if (showCls) cols.push({ label: 'Tỉ lệ ô mức Mạnh trở lên (%)', get: (r) => fmt(r.strong, 1) });
    cols.push({ label: 'Mức tương đối', html: (r) => pill(lvCls ? lvCls[r.level] : 'status-cyan', r.level) });
    const opts = { rowId: (r) => r.id, selected: (r) => r.id === S.district };
    $('rank-top').innerHTML = table(cols, rows.slice(0, 5), opts);
    $('rank-all-summary').textContent = `Xem tất cả ${rows.length} quận / huyện`;
    $('rank-all').innerHTML = table(cols, rows, opts);
    $('rank-all-wrap').hidden = rows.length <= 5;
    document.querySelectorAll('#rank-top tr.click, #rank-all tr.click').forEach((tr) => tr.addEventListener('click', () => {
      const id = Number(tr.dataset.id);
      selectDistrict(S.district === id ? null : id);
    }));
    const sel = rows.find((r) => r.id === S.district);
    const co = $('rank-callout');
    if (sel) {
      co.innerHTML = `📍 Khu vực đang chọn: <strong>${esc(sel.name)}</strong> đang xếp hạng <strong>#${String(sel.rank).padStart(2, '0')}/${rows.length}</strong> với giá trị trung bình <strong>${isDiff() ? sgn(sel.mean, d) : fmt(sel.mean, d)}${u}</strong> (mức phân vị tương đối: <strong>${sel.level}</strong>).`;
      co.hidden = false;
    } else co.hidden = true;
    $('rank-caption').textContent = 'Quận có ít ô lưới (dưới 10 ô, đánh dấu *) thì giá trị trung bình dao động mạnh hơn và kém tin cậy.'
      + (WEATHER.includes(S.ind) ? ' Với T2M và lượng mưa (ERA5-Land, ô gốc khoảng 9 km), nhiều quận nội thành nằm chung một ô nên có giá trị bằng nhau; thứ hạng giữa các quận này không có ý nghĩa.' : '');
  }

  function exportCsv() {
    if (!V) return;
    const modeTxt = S.mode === 'history' ? 'Lịch sử' : viewText();
    const lines = [['Tháng', 'Chỉ số', 'Chế độ', 'Mã ô lưới', 'Quận/huyện', 'Kinh độ', 'Vĩ độ', 'Giá trị'].join(',')];
    Object.entries(V.values).filter(([c]) => inScope(c)).forEach(([c, v]) => {
      const p = CELL[c];
      lines.push([S.month, `"${S.ind} · ${IND[S.ind].name}"`, `"${modeTxt}"`, c, `"${p.district}"`, p.lon.toFixed(5), p.lat.toFixed(5), v].join(','));
    });
    const blob = new Blob(['﻿' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${S.ind}_${S.month}${S.district === null ? '' : '_' + districtName().replace(/\s+/g, '_')}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // ---------------- biểu đồ ----------------
  // Vạch dọc: tháng thiếu Landsat (xám, nét đứt) và tháng đang chọn (trắng)
  const markerPlugin = {
    id: 'markers',
    afterDatasetsDraw(chart, args, o) {
      const { ctx, chartArea: a, scales: { x } } = chart;
      const draw = (m, color, dash, w) => {
        const i = chart.data.labels.indexOf(m);
        if (i < 0) return;
        const px = x.getPixelForValue(i);
        ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.setLineDash(dash);
        ctx.beginPath(); ctx.moveTo(px, a.top); ctx.lineTo(px, a.bottom); ctx.stroke(); ctx.restore();
      };
      (o.bad || []).forEach((m) => draw(m, 'rgba(160,170,180,.6)', [3, 3], 1));
      if (o.selected) draw(o.selected, 'rgba(241,248,255,.85)', [], 2);
    },
  };

  function lineChart(id, labels, datasets, o = {}) {
    const d = prec(S.ind);
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart($(id), {
      type: 'line',
      data: { labels, datasets },
      plugins: [markerPlugin],
      options: {
        responsive: true, maintainAspectRatio: false, animation: false, spanGaps: false,
        interaction: { mode: 'index', intersect: false },
        elements: { point: { radius: 2.5 }, line: { borderWidth: 2, tension: 0.2 } },
        scales: {
          x: { grid: { color: C.grid }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 14, callback: o.xLabel || ((v, i) => labels[i]) } },
          y: { grid: { color: C.grid }, title: { display: true, text: IND[S.ind].name + (IND[S.ind].unit ? ` (${IND[S.ind].unit})` : '') } },
        },
        plugins: {
          legend: { labels: { usePointStyle: true, boxWidth: 8, filter: (it) => !it.text.startsWith('_') } },
          tooltip: { backgroundColor: '#0b1929', borderColor: '#31516d', borderWidth: 1,
            callbacks: { label: (it) => (it.dataset.label.startsWith('_') || it.parsed.y === null ? null : `${it.dataset.label}: ${fmt(it.parsed.y, d + 1)}${unitSfx()}`) } },
          markers: { bad: o.bad || [], selected: o.selected },
        },
      },
    });
  }

  async function refreshHistory() {
    const [s, f] = await Promise.all([
      getJSON(`/api/series/?indicator=${S.ind}&district=${districtParam()}`),
      getJSON(`/api/forecast/?indicator=${S.ind}&district=${districtParam()}`),
    ]);
    const name = IND[S.ind].name;
    $('hist-title').textContent = `Biến động ${name} theo thời gian`;
    const fcMonths = f.forecast.map((r) => r.month), labels = s.months.concat(fcMonths);
    const padF = (a) => a.concat(fcMonths.map(() => null));
    const own = S.district === null ? s.city : s.district;
    const fcLine = new Array(s.months.length - 1).fill(null).concat([own[own.length - 1]], f.forecast.map((r) => r.forecast));
    const ds = [{ label: ALL, data: padF(s.city), borderColor: S.district === null ? C.hist : '#4d6a85', backgroundColor: S.district === null ? C.hist : '#4d6a85' }];
    if (S.district !== null) ds.push({ label: districtName(), data: padF(s.district), borderColor: '#a78bfa', backgroundColor: '#a78bfa' });
    ds.push({ label: 'Dự báo 9–12/2026', data: fcLine, borderColor: C.cyan, backgroundColor: C.cyan, borderDash: [4, 4] });
    lineChart('chart-history', labels, ds, { bad: s.months_without_landsat, selected: S.month });
    $('hist-note').textContent = IND[S.ind].landsat
      ? 'Trung bình chỉ tính trên ô có quan sát Landsat thật (tháng không có ảnh sạch mây để trống). Vạch xám nét đứt: tháng không có ảnh Landsat sạch mây; nét đứt cyan: 4 tháng dự báo cuối 2026; vạch sáng: tháng đang chọn.'
      : WEATHER.includes(S.ind)
        ? 'Đường nét liền: ERA5-Land (tái phân tích khí hậu) 2020–08/2026; nét đứt cyan: 4 tháng dự báo 09–12/2026; vạch sáng: tháng đang chọn. ERA5-Land có ô gốc khoảng 9 km nên khác biệt giữa các quận rất nhỏ.'
        : 'Đường nét liền: quan trắc vệ tinh 2020–08/2026; nét đứt cyan: 4 tháng dự báo 09–12/2026; vạch sáng: tháng đang chọn. NO₂, CO, AOD là lượng trong cột khí quyển, nên đọc theo mùa và theo vùng.';

    // So sánh các năm theo tháng
    const byYear = {};
    s.months.forEach((m, i) => { const [y, mo] = m.split('-'); (byYear[y] = byYear[y] || new Array(12).fill(null))[Number(mo) - 1] = own[i]; });
    const selYear = S.month.slice(0, 4), selMo = S.month.slice(5, 7);
    const yds = Object.keys(byYear).sort().map((y, i) => ({
      label: y, data: byYear[y], borderColor: YEAR_COLORS[i % YEAR_COLORS.length], backgroundColor: YEAR_COLORS[i % YEAR_COLORS.length],
      borderWidth: y === selYear ? 3.5 : 1.6, pointRadius: y === selYear ? 3 : 1.5, order: y === selYear ? 0 : 1,
    }));
    yds.forEach((x) => { if (x.label !== selYear) { x.borderColor += '8c'; } });
    const mlabels = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
    lineChart('chart-years', mlabels, yds, { selected: selMo, xLabel: (v, i) => `T${i + 1}` });
    $('years-note').textContent = `Đường đậm: năm ${selYear} (năm của tháng đang chọn); vạch sáng: tháng ${Number(selMo)}. ${S.district === null ? 'Toàn thành phố' : districtName()}.`;
  }

  async function refreshForecast() {
    const f = await getJSON(`/api/forecast/?indicator=${S.ind}&district=${districtParam()}`);
    const d = prec(S.ind), u = unitSfx(), ind = IND[S.ind];
    $('fc-title').textContent = `Dự báo ${ind.name}`;
    $('fc-sub').textContent = `Lịch sử gần đây, dự báo và khí hậu tham chiếu · ${districtName()}`;
    const fm = f.forecast.map((r) => r.month), labels = f.history.months.concat(fm);
    const nH = f.history.months.length, pad = (a) => new Array(nH).fill(null).concat(a);
    const last = f.history.values[nH - 1];
    lineChart('chart-forecast', labels, [
      { label: 'Lịch sử', data: f.history.values.concat(fm.map(() => null)), borderColor: C.hist, backgroundColor: C.hist },
      { label: '_lower', data: pad(f.forecast.map((r) => r.lower)), borderColor: 'transparent', pointRadius: 0, fill: false },
      { label: 'Khoảng sai số (theo ô)', data: pad(f.forecast.map((r) => r.upper)), borderColor: 'transparent', backgroundColor: 'rgba(22,200,244,.16)', pointRadius: 0, fill: '-1' },
      { label: 'Dự báo', data: new Array(nH - 1).fill(null).concat([last], f.forecast.map((r) => r.forecast)), borderColor: C.cyan, backgroundColor: C.cyan, borderDash: [6, 4] },
      { label: 'Khí hậu', data: pad(f.forecast.map((r) => r.climatology)), borderColor: C.clim, backgroundColor: C.clim, borderDash: [2, 3] },
    ], { selected: S.month, bad: ind.landsat ? META.meta.months_without_landsat : [] });
    $('fc-note').textContent = 'Dải cyan: ' + f.interval_note + ' Đường cyan nối mốc cuối của lịch sử sang các tháng dự báo; vạch sáng: tháng đang chọn.';

    $('fc-table-sub').textContent = `Giá trị dự báo, khí hậu đối sánh và khoảng sai số · ${districtName()}`;
    $('fc-table').innerHTML = table([
      { label: 'Tháng', get: (r) => r.month },
      { label: 'Tầm dự báo', get: (r) => `${r.horizon} tháng` },
      { label: 'Dự báo mô hình', num: true, get: (r) => fmt(r.forecast, d) },
      { label: 'Khí hậu', num: true, get: (r) => fmt(r.climatology, d) },
      { label: 'Chênh lệch', num: true, get: (r) => sgn(r.forecast - r.climatology, d) },
      { label: 'Khoảng sai số [thấp — cao]', get: (r) => `${fmt(r.lower, d)} — ${fmt(r.upper, d)}` },
      { label: 'Mức đánh giá', html: (r) => { const s = evalStatus(S.ind, r.forecast); return pill(s[0], s[1]); } },
    ], f.forecast, { selected: (r) => r.month === S.month });

    $('rel-sub').textContent = `${ind.name} · đánh giá gộp toàn thành phố · áp dụng cùng cho khu vực đang xem: ${districtName()}`;
    const selH = S.mode === 'forecast' ? (META.forecast_months.find((x) => x.month === S.month) || {}).horizon : null;
    $('rel-table').innerHTML = table([
      { label: 'Dự báo trước (tháng)', get: (r) => r.horizon },
      { label: 'Độ tin cậy', html: (r) => pill(REL_CLS[r.reliability] || 'status-mid', r.reliability) },
      { label: 'RMSE mô hình', num: true, get: (r) => fmt(r.rmse_model, d + 2) },
      { label: 'RMSE khí hậu', num: true, get: (r) => fmt(r.rmse_climatology, d + 2) },
      { label: 'So khí hậu (%)', num: true, get: (r) => sgn(r.vs_climatology_pct, 2) },
    ], f.reliability, { selected: (r) => r.horizon === selH });

    const cur = f.forecast.find((r) => r.month === S.month) || f.forecast[0];
    const diff = cur.forecast - cur.climatology;
    const near = { UTFVI: 0.001, NDVI: 0.001, TVDI: 0.001, AOD: 0.001, T2M: 0.1, PRECIP: 2 }[S.ind] ?? 0.2;
    const note = Math.abs(diff) < near
      ? `Dự báo ${S.ind} tháng ${cur.month} tại ${districtName()} xấp xỉ mức khí hậu (${fmt(cur.forecast, d)}${u} so với ${fmt(cur.climatology, d)}${u}).`
      : `Dự báo ${S.ind} tháng ${cur.month} tại ${districtName()} đạt ${fmt(cur.forecast, d)}${u}, ${diff > 0 ? 'cao hơn' : 'thấp hơn'} mức khí hậu ${fmt(Math.abs(diff), d)}${u}.`;
    const warn = {
      CO: 'Mức cải thiện của CO ở dự báo 2–3 tháng (−32%, −34%) là bất thường và không ổn định qua các giai đoạn kiểm thử, không được coi là năng lực dự báo.',
      AOD: 'AOD chỉ tốt hơn khí hậu ở dự báo 1 tháng, mức nhỏ; chuỗi AOD có bước nhảy đầu 2022 chưa rõ nguyên nhân.',
      LST: 'LST: mô hình ngang khí hậu; phần lớn sai số là lệch chung của cả thành phố theo tháng, không dự báo được.',
      NO2: 'NO₂: mô hình ngang hoặc kém khí hậu và dự báo thấp ở các tháng có giá trị cao.',
      TVDI: 'TVDI: mô hình chỉ nhỉnh hơn khí hậu ở dự báo 1 tháng.',
      UTFVI: 'UTFVI: cải thiện so với khí hậu chủ yếu ở dự báo 1 tháng và ở khác biệt giữa các ô.',
      NDVI: 'NDVI là chỉ số mô hình tốt hơn khí hậu rõ nhất; R² cao một phần vì khí hậu đã giải thích phần lớn biến động.',
      T2M: 'T2M: mô hình ngang khí hậu ở dự báo 1 tháng và kém hơn rõ ở 2–4 tháng; dừng sớm thường chỉ giữ 1–3 cây, tức mô hình gần như trở về khí hậu.',
      PRECIP: 'Lượng mưa: mô hình không tốt hơn khí hậu ở giai đoạn nào (2026 kém hơn 21,8%); lượng mưa tháng gần như không dự báo được từ dữ liệu quá khứ.',
    }[S.ind];
    let fold = '';
    const bt = (META.meta.weather_backtest || []).filter((x) => x.indicator === S.ind);
    if (bt.length) {
      fold = '<div class="section-title"><div><h2>Đánh giá 4 giai đoạn (dự báo trước 1 tháng)</h2><p>Kiểm thử lần lượt 2023, 2024, 2025 và 1–8/2026, mỗi lần huấn luyện bằng dữ liệu trước đó</p></div></div>'
        + table([
          { label: 'Giai đoạn', get: (r) => r.fold },
          { label: 'So khí hậu (%)', num: true, get: (r) => sgn(r.vs_climatology_pct, 1) },
          { label: 'Tháng thắng khí hậu', get: (r) => `${r.wins}/${r.months}` },
          { label: 'Số cây (dừng sớm)', get: (r) => r.trees },
        ], bt);
    }
    $('fc-notes').innerHTML = `<div class="callout warning"><strong>Nhận định ${S.ind} (${cur.month}).</strong> ${esc(note)} ${esc(warn)}</div>
      <div class="callout"><strong>Cách diễn giải.</strong> Với phần lớn chỉ số, dự báo gần với khí hậu theo tháng. Mô hình thể hiện tốt hơn khác biệt không gian giữa các khu vực (NDVI, UTFVI) so với biến động chung của toàn thành phố.</div>` + fold;
  }

  async function refreshValidation() {
    const v = await getJSON(`/api/validation/?indicator=${S.ind}&district=${districtParam()}`);
    const d = prec(S.ind), ind = IND[S.ind], m = v.metrics;
    $('val-title').textContent = `Kiểm định 2026 · ${ind.name}`;
    $('val-sub').textContent = `Tháng 1–8/2026 · So sánh thực tế quan trắc, mô hình và khí hậu · ${districtName()}`;
    lineChart('chart-validation', v.months, [
      { label: 'Thực tế', data: v.actual, borderColor: C.actual, backgroundColor: C.actual },
      { label: 'Mô hình', data: v.forecast, borderColor: C.cyan, backgroundColor: C.cyan },
      { label: 'Khí hậu', data: v.climatology, borderColor: C.clim, backgroundColor: C.clim },
    ], { selected: v.months.includes(S.month) ? S.month : null });
    $('val-note').textContent = `Kiểm định cố định trên 8 tháng đầu năm 2026 (dự báo trước 1 tháng); dùng ${fmt(m.n, 0)} cặp ô–tháng. Vạch sáng đánh dấu tháng đang chọn nếu thuộc giai đoạn kiểm định.`;
    const maePct = m.mae_clim ? (m.mae_model / m.mae_clim - 1) * 100 : null;
    const lab = relLabel(S.ind, m.vs_climatology_pct);
    $('val-metrics').innerHTML =
      metricCard('RMSE mô hình (theo ô)', fmt(m.rmse_model, d + 2), `${sgn(m.vs_climatology_pct, 2)}% so với khí hậu`, m.vs_climatology_pct < 0 ? 'delta-up' : 'delta-down')
      + metricCard('MAE mô hình (theo ô)', fmt(m.mae_model, d + 2), maePct === null ? null : `${sgn(maePct, 2)}% so với khí hậu`, maePct < 0 ? 'delta-up' : 'delta-down')
      + metricCard('Đánh giá so với khí hậu', `<span style="font-size:1.25rem">${esc(lab)}</span>`, `R² mô hình ${fmt(m.r2_model, 3)} · khí hậu ${fmt(m.r2_clim, 3)}`, 'delta-off');
    $('val-table-sub').textContent = `Sai số thực tế so với mô hình và khí hậu theo từng tháng · ${districtName()}`;
    const rows = v.months.map((mo, i) => {
      const pct = v.rmse_clim[i] ? (v.rmse_model[i] / v.rmse_clim[i] - 1) * 100 : null;
      return { mo, a: v.actual[i], f: v.forecast[i], c: v.climatology[i], rm: v.rmse_model[i], rc: v.rmse_clim[i], pct, n: v.n[i] };
    });
    $('val-table').innerHTML = table([
      { label: 'Tháng', get: (r) => r.mo },
      { label: 'Thực tế', num: true, get: (r) => fmt(r.a, d + 1) },
      { label: 'Dự báo mô hình', num: true, get: (r) => fmt(r.f, d + 1) },
      { label: 'Khí hậu', num: true, get: (r) => fmt(r.c, d + 1) },
      { label: 'RMSE mô hình', num: true, get: (r) => fmt(r.rm, d + 2) },
      { label: 'RMSE khí hậu', num: true, get: (r) => fmt(r.rc, d + 2) },
      { label: 'So khí hậu (%)', num: true, get: (r) => sgn(r.pct, 2) },
      { label: 'Số ô', get: (r) => fmt(r.n, 0) },
    ], rows, { selected: (r) => r.mo === S.month });
    $('val-table-note').textContent = (ind.landsat ? 'Chỉ tính các ô-tháng có quan sát Landsat sạch mây thật. ' : '')
      + 'Kết quả theo từng tháng chỉ có 8 tháng nên dao động mạnh; không chọn hay loại tháng dựa trên bảng này.';
  }

  // ---------------- giới thiệu ----------------
  async function renderAbout() {
    const t = META.meta.utfvi_thresholds || [], n = classNames();
    const ranges = n.map((_, i) => (i === 0 ? `≤ ${t[0]}` : i === n.length - 1 ? `> ${t[i - 1]}` : `${t[i - 1]} - ${t[i]}`));
    $('utfvi-table').innerHTML = table([
      { label: 'Mức', html: (r) => `<span class="swatch" style="background:${CLASS_COLORS[r.i]}"></span>${esc(r.n)}` },
      { label: 'Khoảng UTFVI', get: (r) => r.r },
    ], n.map((x, i) => ({ i, n: x, r: ranges[i] })));
    const notes = (META.meta.notes || []).concat([
      `Các tháng không có ảnh Landsat đáng tin cậy (giá trị nội suy): ${META.meta.months_without_landsat.join(', ')}.`,
      'Ranh giới quận/huyện trên bản đồ được suy ra từ các ô lưới (răng cưa), không phải ranh giới hành chính chính xác; dùng ranh giới trước sáp nhập 2025.',
      'Mô hình chỉ tốt hơn rõ so với khí hậu ở NDVI và UTFVI (dự báo 1 tháng). LST và NO₂ ngang hoặc kém khí hậu; CO không ổn định.',
      'Các nhãn trạng thái (ví dụ "Nhiệt độ khá cao", "NO₂ cao") dùng ngưỡng tự đặt để đọc nhanh, không phải tiêu chuẩn môi trường chính thức.',
      'NO₂, CO là lượng trong cột khí quyển đo từ vệ tinh, không phải nồng độ không khí mặt đất. Tương quan giữa các chỉ số không phải quan hệ nhân quả.',
      'Nhiệt độ không khí (T2M) và lượng mưa lấy từ ERA5-Land (tái phân tích, ô gốc khoảng 9 km): mỗi tháng chỉ khoảng 140–165 giá trị khác nhau trên 1.981 ô, nên không thể hiện được khác biệt giữa các quận. Mô hình không dự báo hai biến này tốt hơn khí hậu.',
    ]);
    $('about-notes').innerHTML = notes.map((x) => `<div class="note-item">${esc(x)}</div>`).join('');
    try {
      const h = await getJSON('/api/health/');
      $('about-health').textContent = `PostgreSQL ${h.postgresql} · PostGIS ${h.postgis}; ${fmt(h.rows.observation, 0)} dòng quan trắc, ${fmt(h.rows.forecast, 0)} dòng dự báo; API Django, giao diện Leaflet + Chart.js.`;
    } catch (e) { /* không bắt buộc */ }
  }

  init().catch((e) => { console.error(e); $('map-msg').textContent = 'Lỗi tải dữ liệu: ' + e.message; $('map-msg').hidden = false; });
})();
