import pandas as pd

# Simulated battery data
data = pd.DataFrame({
    "battery_id": ["B1","B1","B2","B3"],
    "time": [1,2,1,2],
    "location": ["Station_A","Station_B","Station_A","Station_A"],
    "voltage": [48,47,50,30],
    "temperature": [25,27,26,45]
})

# Fraud detection (same battery, different location quickly)
data["fraud_flag"] = (data["battery_id"].shift() == data["battery_id"]) & \
                     (data["location"] != data["location"].shift())

# Simple health score
data["health"] = 100 - (data["temperature"]*0.5 + abs(50-data["voltage"]))

print(data)
