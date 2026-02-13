import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import os

plt.switch_backend('Agg')

np.random.seed(0)
windowsize = 128
eps = [0.005, 0.008, 0.01, 0.02, 0.03, 0.1]

def fun_eps(x):
    lambdas = (x.sort_values(ignore_index=True)
                 .rolling(2)
                 .apply(lambda y: abs(y.iloc[0] - y.iloc[1]) / y.iloc[0])
                 .dropna())
    res = {}
    for e in eps:
        res[e] = np.count_nonzero(lambdas < e) / lambdas.count()
    return res

def improved_eps(x):    
    newDat = x.sort_values(ignore_index=True)[math.floor(len(x)*(2/3)):]

    lambdas = (newDat.sort_values(ignore_index=True)
                  .rolling(2)
                  .apply(lambda y: abs(y.iloc[0] - y.iloc[1]) / y.iloc[0])
                  .dropna())
    res = {}
    for e in eps:
        res[e] = np.count_nonzero(lambdas < e) / lambdas.count()
    return res

csv_filename = "data/mss_ipd.csv"
input = pd.read_csv(csv_filename)
iat = pd.to_numeric(input["Time"], errors='coerce').dropna() 

print(f"Time range: {iat.min():.6f} to {iat.max():.6f} s")
print(f"Mean IAT: {iat.mean():.6f} s")

results = {e: [] for e in eps}
results_improve = {e: [] for e in eps}

grouped = iat.groupby(np.arange(len(iat)) // windowsize)
for group_id, group_data in grouped:
    score_dict = fun_eps(group_data)
    score_dict_improve = improved_eps(group_data)
    
    for e in eps:
        results[e].append(score_dict[e])
        results_improve[e].append(score_dict_improve[e])


# Prepare data for box plot using improved_eps results
box_data = []
box_labels = []

for epsilon in eps:
    box_data.append(results_improve[epsilon])  # Changed from results to results_improve
    box_labels.append(f'ε={epsilon}')

plt.figure(figsize=(12, 8))
plt.boxplot(box_data, tick_labels=box_labels)
plt.xlabel('ε-threshold')
plt.ylabel('ε-similarity score')
plt.title(f'Improved ε-similarity Distribution Across {len(results_improve[eps[0]])} Windows\n(Window size: {windowsize}, File: {csv_filename})')  # Updated title

plt.ylim(0, 1.0)
plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])

plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

filename_base = os.path.basename(csv_filename).lower()
output_plot_filename = f'epsilon_similarity_boxplot_improved_{filename_base.replace(".csv", "")}.png'  # Added "_improved"
plt.savefig(output_plot_filename, dpi=300, bbox_inches='tight')

output_scores_filename = f'scores_improved_{filename_base.replace(".csv", "")}.csv'  # Added "_improved"
scores_df = pd.DataFrame(results_improve)  # Changed from results to results_improve
scores_df.to_csv(output_scores_filename, index=False)

print(f"\nDataset info:")
print(f"Total traffic points: {len(iat)}")
print(f"Window size: {windowsize}")
print(f"Number of windows: {len(results_improve[eps[0]])}")  # Changed from results to results_improve

print("\nSummary statistics:")
for epsilon in eps:
    values = results_improve[epsilon]  # Changed from results to results_improve
    print(f"ε={epsilon}: min={min(values):.3f}, max={max(values):.3f}, "
          f"mean={np.mean(values):.3f}, median={np.median(values):.3f}, "
          f"std={np.std(values):.3f}")
