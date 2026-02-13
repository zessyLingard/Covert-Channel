import pandas as pd

input_file = "legit_traffic.csv"  
output_file = "legit_traffic_seconds.csv" 

df = pd.read_csv(input_file, header=None)

df[0] = pd.to_numeric(df[0], errors='coerce')

df['Time'] = (df[0] / 1000.0).round(6)

df[['Time']].dropna().to_csv(output_file, index=False)
