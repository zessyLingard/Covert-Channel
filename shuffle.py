import pandas as pd

files = ["data/timings_1_cleaned.csv", "data/timings_2_cleaned.csv", "data/timings_3_cleaned.csv", "data/timings_4_cleaned.csv", "data/timings_5_cleaned.csv", "data/timings_6_cleaned.csv", "data/timings_7_cleaned.csv"]

dfs = [pd.read_csv(file, header=None) for file in files]
combined_df = pd.concat(dfs, ignore_index=True)

combined_df.to_csv("data/all_tau_merged_data.csv", index=False)