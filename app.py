import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    .main { background-color: #080d12; }
    .block-container { padding-top: 1.5rem; }
    h1, h2, h3 { color: #00e5ff !important; }
    .stMetric { background: #0d1520; border-radius: 10px; padding: 10px; border: 1px solid #1a2d45; }
    .stMetric label { color: #4a6480 !important; font-size: 11px !important; letter-spacing: 2px; }
    .stMetric [data-testid="metric-container"] { color: white; }
    div[data-testid="stDataFrame"] { border: 1px solid #1a2d45; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  LOAD DATA + RUN DETECTIONS
# ─────────────────────────────────────────
df = generate_battery_events()
df["health_score"] = df.apply(compute_health_score, axis=1)
alerts = run_all_detections(df)

# ─────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────
col_logo, col_status = st.columns([3, 1])
with col_logo:
    st.markdown("# ⚡ SPIRO GUARDIAN")
    st.markdown("**Real-time Battery Fraud Detection & Network Intelligence**")
with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    st.success(f"🟢 LIVE · {len(df)} events monitored")

st.divider()

# ─────────────────────────────────────────
#  TOP STATS ROW
# ─────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric("🚨 Fraud Alerts", len(alerts), delta="Active now", delta_color="inverse")
with c2:
    critical = len(alerts[alerts["severity"] == "CRITICAL"]) if not alerts.empty else 0
    st.metric("🔴 Critical", critical)
with c3:
    high = len(alerts[alerts["severity"] == "HIGH"]) if not alerts.empty else 0
    st.metric("🟡 High Severity", high)
with c4:
    unique_batteries = df["battery_id"].nunique()
    st.metric("🔋 Batteries Monitored", unique_batteries)
with c5:
    avg_health = round(df["health_score"].mean(), 1)
    st.metric("💚 Avg Health Score", f"{avg_health}/100")

st.divider()

# ─────────────────────────────────────────
#  MAIN CONTENT — TWO COLUMNS
# ─────────────────────────────────────────
left, right = st.columns([1.6, 1])

# ── LEFT: ALERT FEED ─────────────────────
with left:
    st.subheader("🚨 Fraud Alert Feed")

    if alerts.empty:
        st.success("✅ No fraud detected — all assets normal.")
    else:
        for _, row in alerts.iterrows():
            severity = row.get("severity", "HIGH")
            score = row.get("fraud_score", 0)
            fraud_type = row.get("fraud_type", "Unknown")
            battery = row.get("battery_id", "—")
            bike = row.get("bike_id", "—")
            agent = row.get("agent_id", "—")
            location = row.get("location", "—")
            timestamp = str(row.get("timestamp", ""))[:16]

            if severity == "CRITICAL":
                color = "#ff3d5a"
                icon = "🔴"
            else:
                color = "#ffd600"
                icon = "🟡"

            st.markdown(f"""
            <div style="
                background:#0d1520;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 10px;
            ">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:{color}; font-weight:700; font-size:13px; letter-spacing:1px;">
                        {icon} {fraud_type.upper()}
                    </span>
                    <span style="background:rgba(255,255,255,0.08); color:{color};
                                 font-weight:700; padding:2px 10px; border-radius:12px; font-size:13px;">
                        Score: {score}
                    </span>
                </div>
                <div style="color:#d0e8ff; font-size:12px; margin-top:6px;">
                    🔋 <b>{battery}</b> &nbsp;|&nbsp; 🚲 Bike: <b>{bike}</b>
                    &nbsp;|&nbsp; 👤 Agent: <b>{agent}</b>
                </div>
                <div style="color:#4a6480; font-size:11px; margin-top:4px;">
                    📍 {location} &nbsp;·&nbsp; 🕐 {timestamp}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── RIGHT: FRAUD BREAKDOWN CHART ─────────
with right:
    st.subheader("📊 Fraud Type Breakdown")

    if not alerts.empty:
        fraud_counts = alerts["fraud_type"].str.split(" — ").str[0].value_counts().reset_index()
        fraud_counts.columns = ["Fraud Type", "Count"]

        fig = px.bar(
            fraud_counts,
            x="Count",
            y="Fraud Type",
            orientation="h",
            color="Count",
            color_continuous_scale=["#ffd600", "#ff3d5a"],
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="#0d1520",
            plot_bgcolor="#0d1520",
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=10, b=10),
            height=260,
            yaxis_title="",
            xaxis_title="Events",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No fraud data to chart.")

    # ── SEVERITY PIE ─────────────────────
    st.subheader("🎯 Severity Distribution")
    if not alerts.empty:
        sev_counts = alerts["severity"].value_counts().reset_index()
        sev_counts.columns = ["Severity", "Count"]
        color_map = {"CRITICAL": "#ff3d5a", "HIGH": "#ffd600", "MEDIUM": "#00e5ff"}

        fig2 = px.pie(
            sev_counts,
            names="Severity",
            values="Count",
            color="Severity",
            color_discrete_map=color_map,
            template="plotly_dark",
            hole=0.5,
        )
        fig2.update_layout(
            paper_bgcolor="#0d1520",
            margin=dict(l=10, r=10, t=10, b=10),
            height=220,
            legend=dict(font=dict(color="#d0e8ff"))
        )
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
#  FULL FLAGGED ASSETS TABLE
# ─────────────────────────────────────────
st.subheader("🔍 All Flagged Assets")

if not alerts.empty:
    display_alerts = alerts.copy()
    display_alerts["timestamp"] = display_alerts["timestamp"].astype(str).str[:16]

    def color_severity(val):
        if val == "CRITICAL":
            return "color: #ff3d5a; font-weight: bold"
        elif val == "HIGH":
            return "color: #ffd600; font-weight: bold"
        return "color: #00e5ff"

    def color_score(val):
        if val >= 90:
            return "color: #ff3d5a; font-weight: bold"
        elif val >= 70:
            return "color: #ffd600; font-weight: bold"
        return "color: #00e5ff"

    styled = display_alerts.style \
        .map(color_severity, subset=["severity"]) \
        .map(color_score, subset=["fraud_score"])

    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    st.success("✅ No flagged assets.")

st.divider()

# ─────────────────────────────────────────
#  BATTERY HEALTH SECTION
# ─────────────────────────────────────────
st.subheader("🔋 Battery Health Overview")

col_h1, col_h2 = st.columns(2)

with col_h1:
    health_df = df[["battery_id", "voltage", "temperature", "soc", "health_score"]].drop_duplicates("battery_id")

    fig3 = px.scatter(
        health_df,
        x="voltage",
        y="temperature",
        size="health_score",
        color="health_score",
        color_continuous_scale=["#ff3d5a", "#ffd600", "#39ff14"],
        hover_name="battery_id",
        template="plotly_dark",
        title="Voltage vs Temperature (bubble = health score)",
        labels={"voltage": "Voltage (V)", "temperature": "Temp (°C)"}
    )
    fig3.update_layout(
        paper_bgcolor="#0d1520",
        plot_bgcolor="#0d1520",
        height=320,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig3, use_container_width=True)

with col_h2:
    fig4 = px.histogram(
        df,
        x="health_score",
        nbins=10,
        template="plotly_dark",
        title="Health Score Distribution",
        color_discrete_sequence=["#00e5ff"],
        labels={"health_score": "Health Score"}
    )
    fig4.update_layout(
        paper_bgcolor="#0d1520",
        plot_bgcolor="#0d1520",
        height=320,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
#  RAW DATA EXPLORER (optional)
# ─────────────────────────────────────────
with st.expander("🗃️ View Raw Telemetry Data"):
    st.dataframe(df, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#4a6480; font-size:11px; margin-top:20px; letter-spacing:2px;">
    SPIRO GUARDIAN · FRAUD DETECTION INTELLIGENCE · BUILT FOR SPIRO EV NETWORK
</div>
""", unsafe_allow_html=True)
