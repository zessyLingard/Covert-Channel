import pandas as pd

try:
    df = pd.read_csv("legit_traffic.csv")
    filtered_df = df[df["Time"] <= 1]
    print(f"Removed {len(df) - len(filtered_df)} rows. New shape: {filtered_df.shape}")
    filtered_df.to_csv("legit_traffic.csv", index=False)
except Exception as e:
    print(f"ERROR: {e}")