import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from data import generate_battery_events
from detection import run_all_detections, compute_health_score

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Spiro Guardian",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
#  PREMIUM STYLING — OPS CENTER AESTHETIC
# ─────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@700;800&display=swap');

    /* ── GLOBAL RESET ── */
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
        background-color: #03070f;
    }
    .main { background-color: #03070f; }
    .block-container {
        padding-top: 0rem !important;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }

    /* HIDE STREAMLIT NATIVE CHROME */
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }

    /* ── ANIMATED BACKGROUND GRID ── */
    .main::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image:
            linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }

    /* ── TOPBAR / HEADER ── */
    .topbar {
        background: linear-gradient(135deg, #060e1a 0%, #0a1628 50%, #060e1a 100%);
        border-bottom: 1px solid rgba(0,229,255,0.15);
        padding: 18px 32px;
        margin: -1rem -2rem 2rem -2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
    }
    .topbar::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #00e5ff, #7b2fff, transparent);
    }
    .logo-group { display: flex; align-items: center; gap: 16px; }
    .logo-icon {
        width: 44px; height: 44px;
        background: linear-gradient(135deg, #00e5ff22, #7b2fff22);
        border: 1px solid rgba(0,229,255,0.4);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 22px;
    }
    .logo-text {
        font-family: 'Syne', sans-serif;
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 3px;
        background: linear-gradient(90deg, #00e5ff, #7b2fff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
    }
    .logo-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        color: #3a5a7a;
        letter-spacing: 2px;
        margin-top: 2px;
    }
    .status-pill {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(0,229,255,0.06);
        border: 1px solid rgba(0,229,255,0.2);
        border-radius: 50px;
        padding: 6px 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #00e5ff;
        letter-spacing: 1px;
    }
    .pulse-dot {
        width: 7px; height: 7px;
        background: #00e5ff;
        border-radius: 50%;
        animation: pulse 2s ease-in-out infinite;
        box-shadow: 0 0 6px #00e5ff;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.8); }
    }
    .time-display {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #3a5a7a;
        letter-spacing: 1px;
    }

    /* ── KPI CARDS ── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 24px;
    }
    .kpi-card {
        background: linear-gradient(135deg, #080f1c 0%, #0d1828 100%);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 18px 20px;
        position: relative;
        overflow: hidden;
        transition: border-color 0.3s ease, transform 0.2s ease;
    }
    .kpi-card:hover {
        border-color: rgba(0,229,255,0.25);
        transform: translateY(-2px);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
    }
    .kpi-card.critical::before { background: linear-gradient(90deg, #ff3d5a, transparent); }
    .kpi-card.warning::before  { background: linear-gradient(90deg, #ffd600, transparent); }
    .kpi-card.info::before     { background: linear-gradient(90deg, #00e5ff, transparent); }
    .kpi-card.success::before  { background: linear-gradient(90deg, #39ff14, transparent); }
    .kpi-card.purple::before   { background: linear-gradient(90deg, #7b2fff, transparent); }
    .kpi-label {
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 2px;
        color: #3a5a7a;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .kpi-value {
        font-family: 'Syne', sans-serif;
        font-size: 36px;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 6px;
    }
    .kpi-card.critical .kpi-value { color: #ff3d5a; }
    .kpi-card.warning .kpi-value  { color: #ffd600; }
    .kpi-card.info .kpi-value     { color: #00e5ff; }
    .kpi-card.success .kpi-value  { color: #39ff14; }
    .kpi-card.purple .kpi-value   { color: #7b2fff; }
    .kpi-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        color: #3a5a7a;
        letter-spacing: 1px;
    }
    .kpi-icon {
        position: absolute;
        top: 16px; right: 16px;
        font-size: 20px;
        opacity: 0.3;
    }

    /* ── SECTION HEADERS ── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #d0e8ff;
    }
    .section-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        background: rgba(0,229,255,0.1);
        border: 1px solid rgba(0,229,255,0.2);
        color: #00e5ff;
        padding: 2px 10px;
        border-radius: 50px;
        letter-spacing: 1px;
    }

    /* ── ALERT CARDS ── */
    .alert-card {
        background: linear-gradient(135deg, #080f1c 0%, #0c1622 100%);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 8px;
        position: relative;
        overflow: hidden;
        transition: all 0.25s ease;
        cursor: pointer;
    }
    .alert-card:hover {
        background: linear-gradient(135deg, #0d1828 0%, #111e30 100%);
        transform: translateX(4px);
    }
    .alert-card.critical {
        border-left: 3px solid #ff3d5a;
        box-shadow: -4px 0 20px rgba(255,61,90,0.15);
    }
    .alert-card.high {
        border-left: 3px solid #ffd600;
        box-shadow: -4px 0 20px rgba(255,214,0,0.1);
    }
    .alert-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .alert-type {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    .alert-score-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 12px;
        border-radius: 50px;
    }
    .alert-score-badge.critical {
        background: rgba(255,61,90,0.15);
        color: #ff3d5a;
        border: 1px solid rgba(255,61,90,0.3);
    }
    .alert-score-badge.high {
        background: rgba(255,214,0,0.12);
        color: #ffd600;
        border: 1px solid rgba(255,214,0,0.25);
    }
    .alert-meta {
        font-size: 12px;
        color: #7a9ab8;
        margin-bottom: 6px;
    }
    .alert-meta b { color: #c0d8f0; }
    .alert-footer {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        color: #3a5a7a;
        letter-spacing: 0.5px;
    }

    /* ── DRILL DOWN PANEL ── */
    .drill-panel {
        background: linear-gradient(135deg, #07111e 0%, #0a1828 100%);
        border: 1px solid rgba(0,229,255,0.15);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    .drill-panel::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #00e5ff, #7b2fff, transparent);
    }
    .drill-title {
        font-family: 'Syne', sans-serif;
        font-size: 18px;
        font-weight: 800;
        color: #00e5ff;
        letter-spacing: 2px;
        margin-bottom: 4px;
    }
    .drill-subtitle {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        color: #3a5a7a;
        letter-spacing: 2px;
        margin-bottom: 20px;
    }

    /* ── SIDEBAR ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #03070f 0%, #060c18 100%) !important;
        border-right: 1px solid rgba(0,229,255,0.08) !important;
        width: 280px !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding: 1.5rem 1rem;
    }
    .sidebar-logo {
        font-family: 'Syne', sans-serif;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 3px;
        background: linear-gradient(90deg, #00e5ff, #7b2fff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .sidebar-tagline {
        font-family: 'JetBrains Mono', monospace;
        font-size: 9px;
        color: #2a4060;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }
    .sidebar-section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 2.5px;
        color: #2a4060;
        text-transform: uppercase;
        margin: 20px 0 8px 0;
        padding-bottom: 6px;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    section[data-testid="stSidebar"] label {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 12px !important;
        color: #5a7a9a !important;
        letter-spacing: 0.5px !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background: #080f1c !important;
        border: 1px solid rgba(0,229,255,0.15) !important;
        border-radius: 8px !important;
        color: #c0d8f0 !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    section[data-testid="stSidebar"] .stSlider > div {
        padding: 0 !important;
    }

    /* ── BUTTONS ── */
    .stButton > button {
        background: linear-gradient(135deg, #0d1828, #111e30) !important;
        color: #00e5ff !important;
        border: 1px solid rgba(0,229,255,0.2) !important;
        border-radius: 8px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        font-size: 12px !important;
        transition: all 0.2s ease !important;
        padding: 8px 20px !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #0f1e35, #152440) !important;
        border-color: rgba(0,229,255,0.5) !important;
        box-shadow: 0 0 20px rgba(0,229,255,0.1) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* ── TOGGLE ── */
    .stToggle > label { color: #5a7a9a !important; }

    /* ── DATAFRAME ── */
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(0,229,255,0.1) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    div[data-testid="stDataFrame"] thead tr th {
        background: #080f1c !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 10px !important;
        letter-spacing: 1.5px !important;
        color: #3a6a9a !important;
        text-transform: uppercase !important;
        border-bottom: 1px solid rgba(0,229,255,0.1) !important;
    }

    /* ── METRICS override ── */
    [data-testid="metric-container"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }

    /* ── DIVIDERS ── */
    hr {
        border: none !important;
        border-top: 1px solid rgba(255,255,255,0.04) !important;
        margin: 20px 0 !important;
    }

    /* ── EXPANDER ── */
    .streamlit-expanderHeader {
        background: #080f1c !important;
        border: 1px solid rgba(0,229,255,0.1) !important;
        border-radius: 10px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        color: #5a7a9a !important;
    }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: #03070f; }
    ::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.2); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0,229,255,0.4); }

    /* ── TAB NAV ── */
    .stTabs [data-baseweb="tab-list"] {
        background: #060c18 !important;
        border-bottom: 1px solid rgba(0,229,255,0.1) !important;
        gap: 0 !important;
        padding: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        color: #3a5a7a !important;
        padding: 12px 24px !important;
        border-bottom: 2px solid transparent !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        color: #00e5ff !important;
        border-bottom-color: #00e5ff !important;
        background: rgba(0,229,255,0.03) !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding: 20px 0 0 0 !important;
        background: transparent !important;
    }

    /* ── INFO / SUCCESS / WARNING ── */
    .stAlert {
        background: #080f1c !important;
        border-radius: 10px !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }

    /* ── SELECT SLIDER ── */
    .stSelectSlider > div { color: #5a7a9a !important; }

    /* ── Caption ── */
    .stCaption { color: #3a5a7a !important; font-family: 'JetBrains Mono', monospace !important; font-size: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────
if "selected_battery" not in st.session_state:
    st.session_state.selected_battery = None
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

# ─────────────────────────────────────────
#  LOAD DATA + RUN DETECTIONS
# ─────────────────────────────────────────
@st.cache_data(ttl=30)
def load_data(refresh_key=0):
    df = generate_battery_events()
    df["health_score"] = df.apply(compute_health_score, axis=1)
    alerts = run_all_detections(df)
    return df, alerts

df, alerts = load_data(st.session_state.refresh_count)

# ─────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">⚡ Guardian</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Spiro EV · Fraud Intelligence</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">◈ Live Monitoring</div>', unsafe_allow_html=True)
    auto_refresh = st.toggle("Auto-Refresh", value=False)
    refresh_interval = st.select_slider(
        "Interval (seconds)",
        options=[5, 10, 15, 30, 60],
        value=15,
        disabled=not auto_refresh
    )
    if auto_refresh:
        st.caption(f"● LIVE · every {refresh_interval}s")
    else:
        st.caption("○ MANUAL MODE")

    if st.button("↻  Refresh Now", use_container_width=True):
        st.session_state.refresh_count += 1
        st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div class="sidebar-section-label">◈ Filter Alerts</div>', unsafe_allow_html=True)

    severity_options = ["ALL"] + sorted(alerts["severity"].unique().tolist()) if not alerts.empty else ["ALL"]
    selected_severity = st.selectbox("Severity", severity_options)

    fraud_type_options = ["ALL"] + sorted(
        alerts["fraud_type"].str.split(" — ").str[0].unique().tolist()
    ) if not alerts.empty else ["ALL"]
    selected_fraud_type = st.selectbox("Fraud Type", fraud_type_options)

    battery_options = ["ALL"] + sorted(alerts["battery_id"].unique().tolist()) if not alerts.empty else ["ALL"]
    selected_battery_filter = st.selectbox("Battery ID", battery_options)

    min_score = st.slider("Min Fraud Score", 0, 100, 0, step=5)

    st.markdown('<div class="sidebar-section-label">◈ Battery Drill-Down</div>', unsafe_allow_html=True)
    all_batteries = sorted(df["battery_id"].unique().tolist())
    # Preserve current selection across reruns
    current = st.session_state.selected_battery
    options = ["None"] + all_batteries
    # If close was clicked, force back to None/index 0
    if st.session_state.pop("_drill_reset", False):
        current = None
    default_idx = options.index(current) if current in options else 0
    drill_battery = st.selectbox("Select Battery", options, index=default_idx)
    if drill_battery != "None":
        st.session_state.selected_battery = drill_battery
    else:
        st.session_state.selected_battery = None

    st.markdown(f"""
    <div style="position:absolute; bottom:20px; left:16px; right:16px;">
        <div style="font-family:'JetBrains Mono',monospace; font-size:9px; color:#1a3050; letter-spacing:1.5px; text-transform:uppercase;">
            LAST SYNC · {st.session_state.last_refresh}<br>
            CYCLE #{st.session_state.refresh_count:04d}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
#  AUTO-REFRESH LOGIC
# ─────────────────────────────────────────
if auto_refresh:
    import time
    time.sleep(refresh_interval)
    st.session_state.refresh_count += 1
    st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
    st.cache_data.clear()
    st.rerun()

# ─────────────────────────────────────────
#  APPLY FILTERS
# ─────────────────────────────────────────
filtered_alerts = alerts.copy() if not alerts.empty else pd.DataFrame()
if not filtered_alerts.empty:
    if selected_severity != "ALL":
        filtered_alerts = filtered_alerts[filtered_alerts["severity"] == selected_severity]
    if selected_fraud_type != "ALL":
        filtered_alerts = filtered_alerts[filtered_alerts["fraud_type"].str.startswith(selected_fraud_type)]
    if selected_battery_filter != "ALL":
        filtered_alerts = filtered_alerts[filtered_alerts["battery_id"] == selected_battery_filter]
    filtered_alerts = filtered_alerts[filtered_alerts["fraud_score"] >= min_score]

# ─────────────────────────────────────────
#  TOPBAR HEADER
# ─────────────────────────────────────────
active_filters = sum([selected_severity != "ALL", selected_fraud_type != "ALL",
                      selected_battery_filter != "ALL", min_score > 0])

status_text = f"FILTERED · {len(filtered_alerts)} RESULTS" if active_filters else f"MONITORING · {len(df)} EVENTS"
st.markdown(f"""
<div class="topbar">
    <div class="logo-group">
        <div class="logo-icon">⚡</div>
        <div>
            <div class="logo-text">Spiro Guardian</div>
            <div class="logo-sub">Battery Fraud Detection & Network Intelligence</div>
        </div>
    </div>
    <div style="display:flex; align-items:center; gap:16px;">
        <div class="time-display">CYCLE #{st.session_state.refresh_count:04d} · {st.session_state.last_refresh}</div>
        <div class="status-pill">
            <div class="pulse-dot"></div>
            {status_text}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  KPI CARDS (custom HTML)
# ─────────────────────────────────────────
critical_count = len(filtered_alerts[filtered_alerts["severity"] == "CRITICAL"]) if not filtered_alerts.empty else 0
high_count = len(filtered_alerts[filtered_alerts["severity"] == "HIGH"]) if not filtered_alerts.empty else 0
avg_health = round(df["health_score"].mean(), 1) if not df.empty else 0
total_batteries = df["battery_id"].nunique()

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card critical">
        <div class="kpi-icon">🚨</div>
        <div class="kpi-label">Total Alerts</div>
        <div class="kpi-value">{len(filtered_alerts)}</div>
        <div class="kpi-delta">{'↑ FILTERED VIEW' if active_filters else '▸ ACTIVE NOW'}</div>
    </div>
    <div class="kpi-card warning">
        <div class="kpi-icon">🔴</div>
        <div class="kpi-label">Critical</div>
        <div class="kpi-value">{critical_count}</div>
        <div class="kpi-delta">▸ IMMEDIATE ACTION</div>
    </div>
    <div class="kpi-card info">
        <div class="kpi-icon">🟡</div>
        <div class="kpi-label">High Severity</div>
        <div class="kpi-value">{high_count}</div>
        <div class="kpi-delta">▸ REVIEW REQUIRED</div>
    </div>
    <div class="kpi-card success">
        <div class="kpi-icon">🔋</div>
        <div class="kpi-label">Avg Health Score</div>
        <div class="kpi-value">{avg_health}</div>
        <div class="kpi-delta">▸ FLEET AVERAGE</div>
    </div>
    <div class="kpi-card purple">
        <div class="kpi-icon">📡</div>
        <div class="kpi-label">Batteries Tracked</div>
        <div class="kpi-value">{total_batteries}</div>
        <div class="kpi-delta">▸ ACTIVE ASSETS</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  BATTERY DRILL-DOWN PANEL
# ─────────────────────────────────────────
if st.session_state.selected_battery:
    bat_id = st.session_state.selected_battery
    bat_df = df[df["battery_id"] == bat_id].sort_values("timestamp")
    bat_alerts = filtered_alerts[filtered_alerts["battery_id"] == bat_id] if not filtered_alerts.empty else pd.DataFrame()

    st.markdown(f"""
    <div class="drill-panel">
        <div class="drill-title">◈ {bat_id}</div>
        <div class="drill-subtitle">BATTERY FORENSICS · {len(bat_df)} EVENTS · {len(bat_alerts)} ALERTS</div>
    </div>
    """, unsafe_allow_html=True)

    col_soc, col_volt, col_meta = st.columns([2, 2, 1])

    with col_soc:
        fig_soc = go.Figure()
        fig_soc.add_trace(go.Scatter(
            x=bat_df["timestamp"], y=bat_df["soc"],
            mode="lines+markers",
            line=dict(color="#00e5ff", width=2),
            marker=dict(size=6, color="#00e5ff", line=dict(color="rgba(0,229,255,0.53)", width=2)),
            fill="tozeroy",
            fillcolor="rgba(0,229,255,0.05)",
            name="SoC %"
        ))
        fig_soc.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=200, margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False, color="#3a5a7a", tickfont=dict(size=9, family="JetBrains Mono")),
            yaxis=dict(title="SoC %", range=[0, 110], gridcolor="rgba(255,255,255,0.04)",
                       color="#3a5a7a", tickfont=dict(size=9, family="JetBrains Mono")),
            title=dict(text="STATE OF CHARGE", font=dict(size=10, color="#3a5a7a", family="JetBrains Mono"), x=0)
        )
        st.plotly_chart(fig_soc, use_container_width=True)

    with col_volt:
        fig_v = go.Figure()
        fig_v.add_trace(go.Scatter(
            x=bat_df["timestamp"], y=bat_df["voltage"],
            mode="lines+markers",
            line=dict(color="#7b2fff", width=2),
            marker=dict(size=6, color="#7b2fff"),
            fill="tozeroy",
            fillcolor="rgba(123,47,255,0.05)",
            name="Voltage"
        ))
        fig_v.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=200, margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False, color="#3a5a7a", tickfont=dict(size=9, family="JetBrains Mono")),
            yaxis=dict(title="Voltage (V)", gridcolor="rgba(255,255,255,0.04)",
                       color="#3a5a7a", tickfont=dict(size=9, family="JetBrains Mono")),
            title=dict(text="VOLTAGE HISTORY", font=dict(size=10, color="#3a5a7a", family="JetBrains Mono"), x=0)
        )
        st.plotly_chart(fig_v, use_container_width=True)

    with col_meta:
        last_event = bat_df.iloc[-1]
        health = last_event.get("health_score", "—")
        temp = last_event.get("temperature", "—")
        loc = str(last_event.get("location", "—")).replace("Station_", "")
        st.markdown(f"""
        <div style="background:#06101e; border:1px solid rgba(0,229,255,0.1); border-radius:10px; padding:16px; height:100%;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:2px; color:#2a4060; margin-bottom:12px;">LAST READING</div>
            <div style="margin-bottom:10px;">
                <div style="font-size:10px; color:#3a5a7a; margin-bottom:2px;">HEALTH</div>
                <div style="font-family:'Syne',sans-serif; font-size:28px; font-weight:700; color:#39ff14;">{health}</div>
            </div>
            <div style="margin-bottom:10px;">
                <div style="font-size:10px; color:#3a5a7a; margin-bottom:2px;">TEMP</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:16px; color:#ffd600;">{temp}°C</div>
            </div>
            <div>
                <div style="font-size:10px; color:#3a5a7a; margin-bottom:2px;">LOCATION</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:11px; color:#00e5ff;">{loc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if not bat_alerts.empty:
        st.markdown('<div class="section-header" style="margin-top:16px;"><span class="section-title">Active Alerts</span></div>', unsafe_allow_html=True)
        for _, row in bat_alerts.iterrows():
            color = "#ff3d5a" if row["severity"] == "CRITICAL" else "#ffd600"
            sev_class = "critical" if row["severity"] == "CRITICAL" else "high"
            st.markdown(f"""
            <div class="alert-card {sev_class}">
                <div class="alert-top">
                    <span class="alert-type" style="color:{color};">{row['fraud_type'].upper()}</span>
                    <span class="alert-score-badge {sev_class}">SCORE {row['fraud_score']}</span>
                </div>
                <div class="alert-footer">⏱ {str(row['timestamp'])[:16]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success(f"✅ No active alerts for {bat_id}")

    st.markdown('<div style="margin-top:16px;">', unsafe_allow_html=True)
    col_ev, col_close = st.columns([4, 1])
    with col_ev:
        with st.expander("📋 Full Event Log", expanded=False):
            display_bat = bat_df[["timestamp", "event_type", "location", "bike_id",
                                   "agent_id", "soc", "voltage", "temperature", "health_score"]].copy()
            display_bat["timestamp"] = display_bat["timestamp"].astype(str).str[:16]
            st.dataframe(display_bat, use_container_width=True, hide_index=True)
    with col_close:
        if st.button("✕  Close", use_container_width=True):
            st.session_state.selected_battery = None
            st.session_state["_drill_reset"] = True
            st.rerun()

    st.divider()

# ─────────────────────────────────────────
#  TABBED MAIN CONTENT
# ─────────────────────────────────────────
tab_alerts, tab_analytics, tab_health, tab_raw = st.tabs([
    "🚨  Alert Feed",
    "📊  Analytics",
    "🔋  Battery Health",
    "🗃️  Raw Telemetry"
])

# ── TAB 1: ALERT FEED ─────────────────────
with tab_alerts:
    col_feed, col_charts = st.columns([1.5, 1])

    with col_feed:
        st.markdown(f"""
        <div class="section-header">
            <span class="section-title">Fraud Alert Feed</span>
            <span class="section-badge">{len(filtered_alerts)} INCIDENTS</span>
        </div>
        """, unsafe_allow_html=True)

        if filtered_alerts.empty:
            if alerts.empty:
                st.success("✅ No fraud detected — all assets nominal.")
            else:
                st.info("🔍 No alerts match your current filters.")
        else:
            for _, row in filtered_alerts.iterrows():
                severity = row.get("severity", "HIGH")
                score = row.get("fraud_score", 0)
                fraud_type = row.get("fraud_type", "Unknown")
                battery = row.get("battery_id", "—")
                bike = row.get("bike_id", "—")
                agent = row.get("agent_id", "—")
                location = str(row.get("location", "—")).replace("Station_", "")
                timestamp = str(row.get("timestamp", ""))[:16]
                sev_class = "critical" if severity == "CRITICAL" else "high"
                color = "#ff3d5a" if severity == "CRITICAL" else "#ffd600"

                col_card, col_btn = st.columns([7, 1])
                with col_card:
                    st.markdown(f"""
                    <div class="alert-card {sev_class}">
                        <div class="alert-top">
                            <span class="alert-type" style="color:{color};">{fraud_type.upper()}</span>
                            <span class="alert-score-badge {sev_class}">SCORE {score}</span>
                        </div>
                        <div class="alert-meta">
                            🔋 <b>{battery}</b> &nbsp;·&nbsp; 🚲 <b>{bike}</b> &nbsp;·&nbsp; 👤 Agent <b>{agent}</b>
                        </div>
                        <div class="alert-footer">📍 {location} &nbsp;·&nbsp; ⏱ {timestamp}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                    if st.button("⤢", key=f"drill_{battery}_{score}", help=f"Inspect {battery}"):
                        st.session_state.selected_battery = battery
                        st.rerun()

    with col_charts:
        st.markdown("""
        <div class="section-header">
            <span class="section-title">Fraud Breakdown</span>
        </div>
        """, unsafe_allow_html=True)

        if not filtered_alerts.empty:
            fraud_counts = filtered_alerts["fraud_type"].str.split(" — ").str[0].value_counts().reset_index()
            fraud_counts.columns = ["Fraud Type", "Count"]
            fig = px.bar(
                fraud_counts, x="Count", y="Fraud Type", orientation="h",
                color="Count",
                color_continuous_scale=["#ffd600", "#ff3d5a"],
                template="plotly_dark"
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10), height=220,
                yaxis_title="", xaxis_title="Incidents",
                font=dict(family="JetBrains Mono", size=10, color="#5a7a9a"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.04)")
            )
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        <div class="section-header">
            <span class="section-title">Severity Split</span>
        </div>
        """, unsafe_allow_html=True)

        if not filtered_alerts.empty:
            sev_counts = filtered_alerts["severity"].value_counts().reset_index()
            sev_counts.columns = ["Severity", "Count"]
            color_map = {"CRITICAL": "#ff3d5a", "HIGH": "#ffd600", "MEDIUM": "#00e5ff"}
            fig2 = px.pie(
                sev_counts, names="Severity", values="Count", color="Severity",
                color_discrete_map=color_map, template="plotly_dark", hole=0.65
            )
            fig2.update_traces(
                textfont=dict(family="JetBrains Mono", size=10),
                marker=dict(line=dict(color="#03070f", width=3))
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10), height=200,
                legend=dict(font=dict(color="#5a7a9a", size=10, family="JetBrains Mono"),
                            orientation="h", y=-0.05)
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Flagged Assets Table
    st.markdown("""
    <div class="section-header" style="margin-top:10px;">
        <span class="section-title">All Flagged Assets</span>
    </div>
    """, unsafe_allow_html=True)

    if not filtered_alerts.empty:
        display_alerts = filtered_alerts.copy()
        display_alerts["timestamp"] = display_alerts["timestamp"].astype(str).str[:16]

        def color_severity(val):
            if val == "CRITICAL": return "color: #ff3d5a; font-weight: bold"
            elif val == "HIGH": return "color: #ffd600; font-weight: bold"
            return "color: #00e5ff"

        def color_score(val):
            if val >= 90: return "color: #ff3d5a; font-weight: bold"
            elif val >= 70: return "color: #ffd600; font-weight: bold"
            return "color: #00e5ff"

        styled = display_alerts.style.map(color_severity, subset=["severity"]).map(color_score, subset=["fraud_score"])
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        if alerts.empty:
            st.success("✅ No flagged assets.")
        else:
            st.info("🔍 No results match your filters.")

# ── TAB 2: ANALYTICS ──────────────────────
with tab_analytics:
    st.markdown("""
    <div class="section-header">
        <span class="section-title">Network Analytics</span>
        <span class="section-badge">FLEET INTELLIGENCE</span>
    </div>
    """, unsafe_allow_html=True)

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        # Events by station
        station_counts = df["location"].value_counts().reset_index()
        station_counts.columns = ["Station", "Events"]
        station_counts["Station"] = station_counts["Station"].str.replace("Station_", "").str.replace("_", " ")
        fig_st = px.bar(
            station_counts, x="Station", y="Events",
            color="Events", color_continuous_scale=["#0a1e38", "#00e5ff"],
            template="plotly_dark", title="EVENTS BY STATION"
        )
        fig_st.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=280, margin=dict(l=10, r=10, t=36, b=10),
            title_font=dict(size=10, color="#3a5a7a", family="JetBrains Mono"),
            font=dict(family="JetBrains Mono", size=10, color="#5a7a9a"),
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="rgba(255,255,255,0.03)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.03)")
        )
        fig_st.update_traces(marker_line_width=0)
        st.plotly_chart(fig_st, use_container_width=True)

    with col_a2:
        # Event type distribution
        event_counts = df["event_type"].value_counts().reset_index()
        event_counts.columns = ["Event Type", "Count"]
        fig_ev = px.pie(
            event_counts, names="Event Type", values="Count",
            color_discrete_sequence=["#00e5ff", "#7b2fff", "#ff3d5a", "#ffd600", "#39ff14"],
            template="plotly_dark", hole=0.55, title="EVENT TYPE DISTRIBUTION"
        )
        fig_ev.update_traces(
            textfont=dict(family="JetBrains Mono", size=10),
            marker=dict(line=dict(color="#03070f", width=3))
        )
        fig_ev.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            height=280, margin=dict(l=10, r=10, t=36, b=10),
            title_font=dict(size=10, color="#3a5a7a", family="JetBrains Mono"),
            legend=dict(font=dict(color="#5a7a9a", size=10, family="JetBrains Mono"))
        )
        st.plotly_chart(fig_ev, use_container_width=True)

    # Timeline
    timeline_df = df.copy()
    timeline_df["hour"] = timeline_df["timestamp"].dt.floor("h")
    hourly = timeline_df.groupby("hour").size().reset_index(name="Events")

    fig_tl = go.Figure()
    fig_tl.add_trace(go.Scatter(
        x=hourly["hour"], y=hourly["Events"],
        mode="lines",
        line=dict(color="#00e5ff", width=2),
        fill="tozeroy",
        fillcolor="rgba(0,229,255,0.05)",
        name="Events"
    ))
    fig_tl.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=200, margin=dict(l=10, r=10, t=36, b=10),
        title=dict(text="EVENT TIMELINE", font=dict(size=10, color="#3a5a7a", family="JetBrains Mono"), x=0),
        font=dict(family="JetBrains Mono", size=10, color="#5a7a9a"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.03)", showgrid=True),
        yaxis=dict(gridcolor="rgba(255,255,255,0.03)")
    )
    st.plotly_chart(fig_tl, use_container_width=True)

# ── TAB 3: BATTERY HEALTH ─────────────────
with tab_health:
    st.markdown("""
    <div class="section-header">
        <span class="section-title">Battery Health Overview</span>
        <span class="section-badge">DIAGNOSTICS</span>
    </div>
    """, unsafe_allow_html=True)

    col_h1, col_h2 = st.columns(2)
    health_df = df[["battery_id", "voltage", "temperature", "soc", "health_score"]].drop_duplicates("battery_id")

    with col_h1:
        fig3 = px.scatter(
            health_df, x="voltage", y="temperature",
            size="health_score", color="health_score",
            color_continuous_scale=["#ff3d5a", "#ffd600", "#39ff14"],
            hover_name="battery_id", template="plotly_dark",
            title="VOLTAGE vs TEMPERATURE · BUBBLE = HEALTH",
            labels={"voltage": "Voltage (V)", "temperature": "Temp (°C)"}
        )
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=340, margin=dict(l=10, r=10, t=40, b=10),
            title_font=dict(size=10, color="#3a5a7a", family="JetBrains Mono"),
            font=dict(family="JetBrains Mono", size=10, color="#5a7a9a"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            coloraxis_colorbar=dict(tickfont=dict(size=9))
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col_h2:
        fig4 = px.histogram(
            df, x="health_score", nbins=10, template="plotly_dark",
            title="HEALTH SCORE DISTRIBUTION",
            color_discrete_sequence=["#7b2fff"],
            labels={"health_score": "Health Score"}
        )
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=340, margin=dict(l=10, r=10, t=40, b=10),
            title_font=dict(size=10, color="#3a5a7a", family="JetBrains Mono"),
            font=dict(family="JetBrains Mono", size=10, color="#5a7a9a"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            bargap=0.1
        )
        fig4.update_traces(marker_line_width=0)
        st.plotly_chart(fig4, use_container_width=True)

    # Health leaderboard
    st.markdown("""
    <div class="section-header" style="margin-top:8px;">
        <span class="section-title">Battery Health Ranking</span>
    </div>
    """, unsafe_allow_html=True)

    health_rank = health_df.sort_values("health_score", ascending=False).reset_index(drop=True)
    health_rank.index = health_rank.index + 1

    def color_health(val):
        if val >= 90: return "color: #39ff14; font-weight: bold"
        elif val >= 70: return "color: #ffd600"
        return "color: #ff3d5a; font-weight: bold"

    styled_health = health_rank.style.map(color_health, subset=["health_score"])
    st.dataframe(styled_health, use_container_width=True)

# ── TAB 4: RAW TELEMETRY ──────────────────
with tab_raw:
    st.markdown("""
    <div class="section-header">
        <span class="section-title">Raw Telemetry Explorer</span>
        <span class="section-badge">ALL EVENTS</span>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search_term = st.text_input("⌕  Search battery, bike, agent or location", "", placeholder="e.g. B-0559 or Station_Huye")
    with col_s2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.metric("Total Records", len(df))

    raw_display = df.copy()
    if search_term:
        mask = raw_display.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        raw_display = raw_display[mask]
        st.caption(f"↳ {len(raw_display)} rows matching  '{search_term}'")

    st.dataframe(raw_display, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────
st.markdown(f"""
<div style="
    text-align: center;
    padding: 24px 0 12px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #1a3050;
    letter-spacing: 2px;
    border-top: 1px solid rgba(255,255,255,0.03);
    margin-top: 20px;
    text-transform: uppercase;
">
    Spiro Guardian &nbsp;·&nbsp; Battery Fraud Detection Intelligence &nbsp;·&nbsp; Built for Spiro EV Network
    &nbsp;·&nbsp; Last sync {st.session_state.last_refresh}
</div>
""", unsafe_allow_html=True)
