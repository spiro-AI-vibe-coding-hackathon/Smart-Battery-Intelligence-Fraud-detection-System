import pandas as pd
from data import BATTERY_BIKE_REGISTRY, STATION_DISTANCES

# ─────────────────────────────────────────
#  FRAUD DETECTION ENGINE
#  Each function checks one fraud signal
#  and returns rows that are flagged.
# ─────────────────────────────────────────

def detect_unattached_departure(df):
    """
    FRAUD 1: Battery left a swap station without being
    attached to a bike. Signals agent stole the battery.
    """
    flagged = df[
        (df["event_type"] == "departure") &
        (df["bike_attached"] == False)
    ].copy()
    flagged["fraud_type"] = "Agent Fraud — Unattached Departure"
    flagged["severity"] = "CRITICAL"
    flagged["fraud_score"] = 98
    return flagged


def detect_illegal_charging(df):
    """
    FRAUD 2: Battery is charging at a location that is NOT
    a registered Spiro station or warehouse.
    """
    flagged = df[
        (df["event_type"] == "charging") &
        (df["charging_location_known"] == False)
    ].copy()
    flagged["fraud_type"] = "Illegal Charging — Unknown Location"
    flagged["severity"] = "CRITICAL"
    flagged["fraud_score"] = 95
    return flagged


def detect_mismatched_battery(df):
    """
    FRAUD 3: A bike is running a battery that was not
    officially assigned to it in the registry.
    """
    rows = []
    for _, row in df.iterrows():
        assigned_bike = BATTERY_BIKE_REGISTRY.get(row["battery_id"])
        if assigned_bike and row["bike_id"] != assigned_bike:
            flagged_row = row.copy()
            flagged_row["fraud_type"] = f"Mismatched Battery — Expected {assigned_bike}"
            flagged_row["severity"] = "HIGH"
            flagged_row["fraud_score"] = 82
            rows.append(flagged_row)
    return pd.DataFrame(rows)


def detect_long_dwell(df, threshold_days=7):
    """
    FRAUD 4: A bike has been holding a battery for more than
    7 days without returning it for a swap. Signals illegal
    use or hoarding.
    """
    flagged = df[df["days_with_bike"] > threshold_days].copy()
    flagged["fraud_type"] = f"Long Dwell — Battery held >{threshold_days} days"
    flagged["severity"] = "HIGH"
    flagged["fraud_score"] = 79
    return flagged


def detect_velocity_anomaly(df, max_speed_kmh=60):
    """
    FRAUD 5: The same battery appears at two different stations
    that are physically too far apart in too short a time.
    Signals GPS spoofing or cloned battery ID.
    """
    flagged_rows = []
    battery_groups = df.sort_values("timestamp").groupby("battery_id")

    for battery_id, group in battery_groups:
        group = group.reset_index(drop=True)
        for i in range(len(group) - 1):
            loc1 = group.loc[i, "location"]
            loc2 = group.loc[i + 1, "location"]
            t1 = group.loc[i, "timestamp"]
            t2 = group.loc[i + 1, "timestamp"]

            pair = (loc1, loc2)
            pair_rev = (loc2, loc1)
            distance = STATION_DISTANCES.get(pair) or STATION_DISTANCES.get(pair_rev)

            if distance:
                hours = (t2 - t1).total_seconds() / 3600
                if hours > 0:
                    speed = distance / hours
                    if speed > max_speed_kmh:
                        row = group.loc[i + 1].copy()
                        row["fraud_type"] = f"Velocity Anomaly — {speed:.0f} km/h impossible"
                        row["severity"] = "HIGH"
                        row["fraud_score"] = 75
                        flagged_rows.append(row)

    return pd.DataFrame(flagged_rows)


def run_all_detections(df):
    """
    Runs all 5 fraud detectors and combines results
    into one unified alerts DataFrame.
    """
    results = []

    detectors = [
        detect_unattached_departure,
        detect_illegal_charging,
        detect_mismatched_battery,
        detect_long_dwell,
        detect_velocity_anomaly,
    ]

    for detector in detectors:
        result = detector(df)
        if not result.empty:
            results.append(result)

    if results:
        alerts = pd.concat(results, ignore_index=True)
        # Keep only useful display columns
        cols = ["battery_id", "bike_id", "agent_id", "timestamp",
                "location", "fraud_type", "severity", "fraud_score", "soc"]
        alerts = alerts[[c for c in cols if c in alerts.columns]]
        alerts = alerts.sort_values("fraud_score", ascending=False).reset_index(drop=True)
        return alerts
    else:
        return pd.DataFrame()


def compute_health_score(row):
    """
    Simple battery health score (0-100).
    Penalises high temperature and low/abnormal voltage.
    """
    temp_penalty = max(0, (row["temperature"] - 30) * 2)
    voltage_penalty = abs(50 - row["voltage"]) * 3
    score = 100 - temp_penalty - voltage_penalty
    return round(max(0, min(100, score)), 1)
