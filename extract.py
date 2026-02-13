import pandas as pd

df = pd.read_csv("legit.csv")

if "Time" in df.columns:
    ts = df["Time"].astype(float)
elif "frame.time_relative" in df.columns:
    ts = df["frame.time_relative"].astype(float)
else:
    raise SystemExit("Timestamp column not found in legit.csv; open it and check column names")

pd.DataFrame({"Time": ts.values}).to_csv("legit_traffic.csv", index=False, float_format='%.6f')
print("legit_traffic.csv created with timestamps in seconds (6 decimal places)")