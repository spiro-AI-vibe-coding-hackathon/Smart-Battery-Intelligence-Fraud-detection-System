import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ─────────────────────────────────────────
#  SIMULATED SPIRO NETWORK DATA
# ─────────────────────────────────────────

KNOWN_STATIONS = [
    "Station_Kimironko", "Station_Nyabugogo", "Station_Kicukiro",
    "Station_Musanze", "Station_Huye", "Station_Warehouse_A"
]

def generate_battery_events():
    np.random.seed(42)
    base_time = datetime(2026, 4, 10, 8, 0, 0)

    records = []

    # ── Normal batteries ──────────────────
    for i in range(1, 8):
        for j in range(6):
            records.append({
                "battery_id": f"B-{100+i:04d}",
                "bike_id": f"BK-{200+i:04d}",
                "agent_id": f"AG-{10+i:03d}",
                "timestamp": base_time + timedelta(hours=j*4 + i),
                "location": np.random.choice(KNOWN_STATIONS),
                "event_type": np.random.choice(["swap", "charge_complete", "check_in"]),
                "soc": np.random.randint(80, 100),
                "voltage": np.random.uniform(47, 52),
                "temperature": np.random.uniform(22, 30),
                "bike_attached": True,
                "charging_location_known": True,
                "days_with_bike": np.random.randint(0, 3),
            })

    # ── FRAUD 1: Battery leaves station without bike attachment ──
    records.append({
        "battery_id": "B-2291",
        "bike_id": None,
        "agent_id": "AG-114",
        "timestamp": base_time + timedelta(hours=30),
        "location": "Station_Kimironko",
        "event_type": "departure",
        "soc": 100,
        "voltage": 50.2,
        "temperature": 25.0,
        "bike_attached": False,          # ← FRAUD SIGNAL
        "charging_location_known": True,
        "days_with_bike": 0,
    })

    # ── FRAUD 2: Battery charging at unknown location ──
    records.append({
        "battery_id": "B-0883",
        "bike_id": "BK-0301",
        "agent_id": "AG-055",
        "timestamp": base_time + timedelta(hours=20),
        "location": "Private_Residence_GPS_-1.944_30.061",
        "event_type": "charging",
        "soc": 47,
        "voltage": 44.1,
        "temperature": 31.0,
        "bike_attached": True,
        "charging_location_known": False,  # ← FRAUD SIGNAL
        "days_with_bike": 2,
    })

    # ── FRAUD 3: Bike running battery not assigned to it ──
    records.append({
        "battery_id": "B-1107",
        "bike_id": "BK-0422",       # ← battery was assigned to BK-0318
        "agent_id": "AG-078",
        "timestamp": base_time + timedelta(hours=15),
        "location": "Station_Nyabugogo",
        "event_type": "swap",
        "soc": 62,
        "voltage": 46.5,
        "temperature": 28.0,
        "bike_attached": True,
        "charging_location_known": True,
        "days_with_bike": 1,
    })

    # ── FRAUD 4: Bike holding battery for over 7 days ──
    records.append({
        "battery_id": "B-0441",
        "bike_id": "BK-0777",
        "agent_id": "AG-033",
        "timestamp": base_time + timedelta(hours=5),
        "location": "Station_Musanze",
        "event_type": "check_in",
        "soc": 38,
        "voltage": 43.0,
        "temperature": 35.0,
        "bike_attached": True,
        "charging_location_known": True,
        "days_with_bike": 9,              # ← FRAUD SIGNAL
    })

    # ── FRAUD 5: Velocity impossibility (same battery, 2 stations too far apart) ──
    records.append({
        "battery_id": "B-0559",
        "bike_id": "BK-0199",
        "agent_id": "AG-020",
        "timestamp": base_time + timedelta(hours=11),
        "location": "Station_Kicukiro",
        "event_type": "swap",
        "soc": 91,
        "voltage": 51.0,
        "temperature": 24.0,
        "bike_attached": True,
        "charging_location_known": True,
        "days_with_bike": 0,
    })
    records.append({
        "battery_id": "B-0559",
        "bike_id": "BK-0200",
        "agent_id": "AG-021",
        "timestamp": base_time + timedelta(hours=11, minutes=35),  # 35 mins later, 80km away
        "location": "Station_Huye",
        "event_type": "swap",
        "soc": 88,
        "voltage": 50.5,
        "temperature": 24.5,
        "bike_attached": True,
        "charging_location_known": True,
        "days_with_bike": 0,
    })

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


# Battery-to-bike assignment registry
BATTERY_BIKE_REGISTRY = {
    "B-1107": "BK-0318",   # B-1107 is officially assigned to BK-0318
    "B-2291": "BK-0501",
    "B-0883": "BK-0301",
    "B-0441": "BK-0112",
    "B-0559": "BK-0199",
}

# Station distance matrix (km) — simplified
STATION_DISTANCES = {
    ("Station_Kicukiro", "Station_Huye"): 130,
    ("Station_Kimironko", "Station_Musanze"): 90,
    ("Station_Nyabugogo", "Station_Huye"): 120,
}
