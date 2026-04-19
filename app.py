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
    layout="wide"
)

# ─────────────────────────────────────────
#  CUSTOM STYLING
# ─────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }
    .main { background-color: #080d12; }
    .block-container { padding-top: 1.5rem; }
    h1, h2, h3 { color: #00e5ff !important; font-family: 'Rajdhani', sans-serif !important; }
    .stMetric { background: #0d1520; border-radius: 10px; padding: 10px; border: 1px solid #1a2d45; }
    .stMetric label { color: #4a6480 !important; font-size: 11px !important; letter-spacing: 2px; }
    .stMetric [data-testid="metric-container"] { color: white; }
    div[data-testid="stDataFrame"] { border: 1px solid #1a2d45; border-radius: 8px; }
    .drill-panel { background: #0d1a28; border: 1px solid #00e5ff44; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
    section[data-testid="stSidebar"] { background: #060b10 !important; border-right: 1px solid #1a2d45; }
    section[data-testid="stSidebar"] label { color: #00e5ff !important; font-family: 'Rajdhani', sans-serif !important; }
    .stButton > button { background: #0d1520 !important; color: #00e5ff !important; border: 1px solid #00e5ff44 !important; border-radius: 8px !important; font-family: 'Rajdhani', sans-serif !important; letter-spacing: 1px !important; font-weight: 600 !important; }
    .stButton > button:hover { background: #00e5ff22 !important; border-color: #00e5ff !important; }
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
#  SIDEBAR — FILTERS + CONTROLS
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ SPIRO GUARDIAN")
    st.markdown("---")

    # Auto-refresh
    st.markdown("### 🔄 Live Monitoring")
    auto_refresh = st.toggle("Enable Auto-Refresh", value=False)
    refresh_interval = st.select_slider(
        "Refresh interval (seconds)",
        options=[5, 10, 15, 30, 60],
        value=15,
        disabled=not auto_refresh
    )
    if auto_refresh:
        st.caption(f"🟢 Live · refreshing every {refresh_interval}s")
    else:
        st.caption("⚪ Manual mode")

    if st.button("🔃 Refresh Now", use_container_width=True):
        st.session_state.refresh_count += 1
        st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    # Filters
    st.markdown("### 🔍 Filter Alerts")
    severity_options = ["ALL"] + sorted(alerts["severity"].unique().tolist()) if not alerts.empty else ["ALL"]
    selected_severity = st.selectbox("Severity", severity_options)

    fraud_type_options = ["ALL"] + sorted(
        alerts["fraud_type"].str.split(" — ").str[0].unique().tolist()
    ) if not alerts.empty else ["ALL"]
    selected_fraud_type = st.selectbox("Fraud Type", fraud_type_options)

    battery_options = ["ALL"] + sorted(alerts["battery_id"].unique().tolist()) if not alerts.empty else ["ALL"]
    selected_battery_filter = st.selectbox("Battery ID", battery_options)

    min_score = st.slider("Min Fraud Score", 0, 100, 0, step=5)

    st.markdown("---")

    # Drill-down selector
    st.markdown("### 🔋 Battery Drill-Down")
    all_batteries = sorted(df["battery_id"].unique().tolist())
    drill_battery = st.selectbox("Select Battery", ["None"] + all_batteries, index=0)
    if drill_battery != "None":
        st.session_state.selected_battery = drill_battery
    else:
        st.session_state.selected_battery = None

    st.markdown("---")
    st.markdown(
        f"<div style='color:#4a6480; font-size:11px; letter-spacing:1px;'>"
        f"Last refresh: {st.session_state.last_refresh}<br>"
        f"Refresh #{st.session_state.refresh_count}</div>",
        unsafe_allow_html=True
    )

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
#  HEADER
# ─────────────────────────────────────────
col_logo, col_status = st.columns([3, 1])
with col_logo:
    st.markdown("# ⚡ SPIRO GUARDIAN")
    st.markdown("**Real-time Battery Fraud Detection & Network Intelligence**")
with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    active_filters = sum([selected_severity != "ALL", selected_fraud_type != "ALL",
                          selected_battery_filter != "ALL", min_score > 0])
    if active_filters:
        st.warning(f"🔍 {active_filters} filter(s) active · {len(filtered_alerts)} shown")
    else:
        st.success(f"🟢 LIVE · {len(df)} events monitored")

st.divider()

# ─────────────────────────────────────────
#  TOP STATS ROW
# ─────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    delta_label = f"{len(alerts) - len(filtered_alerts)} filtered" if len(filtered_alerts) != len(alerts) else "Active now"
    st.metric("🚨 Fraud Alerts", len(filtered_alerts), delta=delta_label, delta_color="inverse")
with c2:
    critical = len(filtered_alerts[filtered_alerts["severity"] == "CRITICAL"]) if not filtered_alerts.empty else 0
    st.metric("🔴 Critical", critical)
with c3:
    high = len(filtered_alerts[filtered_alerts["severity"] == "HIGH"]) if not filtered_alerts.empty else 0
    st.metric("🟡 High Severity", high)
with c4:
    st.metric("🔋 Batteries Monitored", df["battery_id"].nunique())
with c5:
    st.metric("💚 Avg Health Score", f"{round(df['health_score'].mean(), 1)}/100")

st.divider()

# ─────────────────────────────────────────
#  BATTERY DRILL-DOWN PANEL
# ─────────────────────────────────────────
if st.session_state.selected_battery:
    bat_id = st.session_state.selected_battery
    bat_df = df[df["battery_id"] == bat_id].sort_values("timestamp")
    bat_alerts = alerts[alerts["battery_id"] == bat_id] if not alerts.empty else pd.DataFrame()

    st.markdown(f"""
    <div class="drill-panel">
        <div style="color:#00e5ff; font-family:'Rajdhani',sans-serif; font-size:20px; font-weight:700; letter-spacing:2px; margin-bottom:4px;">
            🔋 BATTERY DRILL-DOWN · {bat_id}
        </div>
        <div style="color:#4a6480; font-size:12px; letter-spacing:1px;">
            {len(bat_df)} events recorded · {len(bat_alerts)} alert(s) flagged
        </div>
    </div>
    """, unsafe_allow_html=True)

    dd1, dd2, dd3, dd4 = st.columns(4)
    with dd1:
        st.metric("Events", len(bat_df))
    with dd2:
        st.metric("Avg Voltage", f"{bat_df['voltage'].mean():.2f} V")
    with dd3:
        st.metric("Avg Temp", f"{bat_df['temperature'].mean():.1f} °C")
    with dd4:
        st.metric("Avg SoC", f"{bat_df['soc'].mean():.0f}%")

    drill_left, drill_right = st.columns(2)
    with drill_left:
        fig_drill = go.Figure()
        fig_drill.add_trace(go.Scatter(
            x=bat_df["timestamp"], y=bat_df["voltage"],
            mode="lines+markers", name="Voltage (V)",
            line=dict(color="#00e5ff", width=2), marker=dict(size=6)
        ))
        fig_drill.add_trace(go.Scatter(
            x=bat_df["timestamp"], y=bat_df["temperature"],
            mode="lines+markers", name="Temp (°C)",
            line=dict(color="#ffd600", width=2), marker=dict(size=6), yaxis="y2"
        ))
        fig_drill.update_layout(
            template="plotly_dark", paper_bgcolor="#0d1520", plot_bgcolor="#0d1520",
            height=260, margin=dict(l=10, r=10, t=30, b=10),
            title=dict(text="Voltage & Temperature Over Time", font=dict(color="#00e5ff", size=13)),
            yaxis=dict(title="Voltage (V)", color="#00e5ff"),
            yaxis2=dict(title="Temp (°C)", overlaying="y", side="right", color="#ffd600"),
            legend=dict(font=dict(color="#d0e8ff"), orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_drill, use_container_width=True)

    with drill_right:
        fig_soc = go.Figure()
        fig_soc.add_trace(go.Bar(
            x=bat_df["timestamp"], y=bat_df["soc"],
            name="SoC (%)", marker_color="#39ff14", opacity=0.8
        ))
        fig_soc.update_layout(
            template="plotly_dark", paper_bgcolor="#0d1520", plot_bgcolor="#0d1520",
            height=260, margin=dict(l=10, r=10, t=30, b=10),
            title=dict(text="State of Charge (SoC) History", font=dict(color="#00e5ff", size=13)),
            yaxis=dict(title="SoC (%)", range=[0, 110]), showlegend=False
        )
        st.plotly_chart(fig_soc, use_container_width=True)

    st.markdown("**📋 Event Log**")
    display_bat = bat_df[["timestamp", "event_type", "location", "bike_id",
                           "agent_id", "soc", "voltage", "temperature", "health_score"]].copy()
    display_bat["timestamp"] = display_bat["timestamp"].astype(str).str[:16]
    st.dataframe(display_bat, use_container_width=True, hide_index=True)

    if not bat_alerts.empty:
        st.markdown(f"**🚨 Alerts for {bat_id}**")
        for _, row in bat_alerts.iterrows():
            color = "#ff3d5a" if row["severity"] == "CRITICAL" else "#ffd600"
            st.markdown(f"""
            <div style="background:#0d1520; border-left:4px solid {color};
                        border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                <span style="color:{color}; font-weight:700; font-size:13px;">
                    {row['fraud_type'].upper()}
                </span>
                <span style="color:#4a6480; font-size:11px; margin-left:12px;">
                    Score: {row['fraud_score']} · {str(row['timestamp'])[:16]}
                </span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success(f"✅ No alerts for {bat_id}")

    if st.button("✖ Close Drill-Down"):
        st.session_state.selected_battery = None
        st.rerun()

    st.divider()

# ─────────────────────────────────────────
#  MAIN CONTENT — TWO COLUMNS
# ─────────────────────────────────────────
left, right = st.columns([1.6, 1])

with left:
    st.subheader("🚨 Fraud Alert Feed")
    if filtered_alerts.empty:
        if alerts.empty:
            st.success("✅ No fraud detected — all assets normal.")
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
            location = row.get("location", "—")
            timestamp = str(row.get("timestamp", ""))[:16]
            color = "#ff3d5a" if severity == "CRITICAL" else "#ffd600"
            icon = "🔴" if severity == "CRITICAL" else "🟡"

            col_card, col_btn = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
                <div style="background:#0d1520; border-left:4px solid {color}; border-radius:8px; padding:12px 16px; margin-bottom:4px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:{color}; font-weight:700; font-size:13px; letter-spacing:1px;">{icon} {fraud_type.upper()}</span>
                        <span style="background:rgba(255,255,255,0.08); color:{color}; font-weight:700; padding:2px 10px; border-radius:12px; font-size:13px;">Score: {score}</span>
                    </div>
                    <div style="color:#d0e8ff; font-size:12px; margin-top:6px;">
                        🔋 <b>{battery}</b> &nbsp;|&nbsp; 🚲 Bike: <b>{bike}</b> &nbsp;|&nbsp; 👤 Agent: <b>{agent}</b>
                    </div>
                    <div style="color:#4a6480; font-size:11px; margin-top:4px;">📍 {location} &nbsp;·&nbsp; 🕐 {timestamp}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button("🔍", key=f"drill_{battery}_{score}", help=f"Drill into {battery}"):
                    st.session_state.selected_battery = battery
                    st.rerun()

with right:
    st.subheader("📊 Fraud Type Breakdown")
    if not filtered_alerts.empty:
        fraud_counts = filtered_alerts["fraud_type"].str.split(" — ").str[0].value_counts().reset_index()
        fraud_counts.columns = ["Fraud Type", "Count"]
        fig = px.bar(fraud_counts, x="Count", y="Fraud Type", orientation="h",
                     color="Count", color_continuous_scale=["#ffd600", "#ff3d5a"], template="plotly_dark")
        fig.update_layout(paper_bgcolor="#0d1520", plot_bgcolor="#0d1520", showlegend=False,
                          coloraxis_showscale=False, margin=dict(l=10, r=10, t=10, b=10),
                          height=260, yaxis_title="", xaxis_title="Events")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No fraud data to chart.")

    st.subheader("🎯 Severity Distribution")
    if not filtered_alerts.empty:
        sev_counts = filtered_alerts["severity"].value_counts().reset_index()
        sev_counts.columns = ["Severity", "Count"]
        color_map = {"CRITICAL": "#ff3d5a", "HIGH": "#ffd600", "MEDIUM": "#00e5ff"}
        fig2 = px.pie(sev_counts, names="Severity", values="Count", color="Severity",
                      color_discrete_map=color_map, template="plotly_dark", hole=0.5)
        fig2.update_layout(paper_bgcolor="#0d1520", margin=dict(l=10, r=10, t=10, b=10),
                           height=220, legend=dict(font=dict(color="#d0e8ff")))
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
#  FULL FLAGGED ASSETS TABLE
# ─────────────────────────────────────────
st.subheader("🔍 All Flagged Assets")
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
    st.success("✅ No flagged assets.") if alerts.empty else st.info("🔍 No results match your filters.")

st.divider()

# ─────────────────────────────────────────
#  BATTERY HEALTH SECTION
# ─────────────────────────────────────────
st.subheader("🔋 Battery Health Overview")
col_h1, col_h2 = st.columns(2)

with col_h1:
    health_df = df[["battery_id", "voltage", "temperature", "soc", "health_score"]].drop_duplicates("battery_id")
    fig3 = px.scatter(health_df, x="voltage", y="temperature", size="health_score", color="health_score",
                      color_continuous_scale=["#ff3d5a", "#ffd600", "#39ff14"], hover_name="battery_id",
                      template="plotly_dark", title="Voltage vs Temperature (bubble = health score)",
                      labels={"voltage": "Voltage (V)", "temperature": "Temp (°C)"})
    fig3.update_layout(paper_bgcolor="#0d1520", plot_bgcolor="#0d1520", height=320, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig3, use_container_width=True)

with col_h2:
    fig4 = px.histogram(df, x="health_score", nbins=10, template="plotly_dark",
                        title="Health Score Distribution", color_discrete_sequence=["#00e5ff"],
                        labels={"health_score": "Health Score"})
    fig4.update_layout(paper_bgcolor="#0d1520", plot_bgcolor="#0d1520", height=320, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
#  RAW DATA EXPLORER
# ─────────────────────────────────────────
with st.expander("🗃️ View Raw Telemetry Data"):
    search_term = st.text_input("🔎 Search by battery, bike, agent or location", "")
    raw_display = df.copy()
    if search_term:
        mask = raw_display.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        raw_display = raw_display[mask]
        st.caption(f"{len(raw_display)} rows match '{search_term}'")
    st.dataframe(raw_display, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; color:#4a6480; font-size:11px; margin-top:20px; letter-spacing:2px;">
    SPIRO GUARDIAN · FRAUD DETECTION INTELLIGENCE · BUILT FOR SPIRO EV NETWORK
    &nbsp;·&nbsp; Last updated: {st.session_state.last_refresh}
</div>
""", unsafe_allow_html=True)
