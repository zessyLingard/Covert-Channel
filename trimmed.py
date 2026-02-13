import pandas as pd

files = ["timings_1_cleaned.csv", "timings_2_cleaned.csv", "timings_3_cleaned.csv", "timings_4_cleaned.csv", "timings_5_cleaned.csv", "timings_6_cleaned.csv", "timings_7_cleaned.csv"]
window_size = 2000

for file in files:
    df = pd.read_csv(file, header=None)
    num_windows = len(df) // window_size
    trimmed_len = num_windows * window_size
    
    trimmed_df = df.head(trimmed_len)
    
    trimmed_df.to_csv(file, index=False, header=False)
    