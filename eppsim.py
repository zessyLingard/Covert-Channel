import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import os

plt.switch_backend('Agg')

np.random.seed(0)
windowsize = 2000
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

csv_filename = "data/legit_traffic_seconds.csv"
input = pd.read_csv(csv_filename, encoding = "utf-16")
iat = pd.to_numeric(input["IPDs"], errors='coerce').dropna() 

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

# ========================
# SỬA LẠI PHẦN VẼ BIỂU ĐỒ (Dùng thuật toán gốc)
# ========================
box_data = []
box_labels = []

for epsilon in eps:
    # ĐỔI LẠI THÀNH `results` THAY VÌ `results_improve`
    box_data.append(results[epsilon])  
    box_labels.append(f'ε={epsilon}')

plt.figure(figsize=(12, 8))
plt.boxplot(box_data, tick_labels=box_labels)
plt.xlabel('ε-threshold')
plt.ylabel('ε-similarity score')

# Sửa lại tiêu đề
plt.title(f'Original ε-similarity Distribution Across {len(results[eps[0]])} Windows\n(Window size: {windowsize}, File: {csv_filename})') 

plt.ylim(0, 1.0)
plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])

plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

filename_base = os.path.basename(csv_filename).lower()
# Đổi tên file output thành "original"
output_plot_filename = f'epsilon_similarity_boxplot_original_{filename_base.replace(".csv", "")}.png'  
plt.savefig(output_plot_filename, dpi=300, bbox_inches='tight')

output_scores_filename = f'scores_original_{filename_base.replace(".csv", "")}.csv'  
# Xuất dữ liệu từ `results`
scores_df = pd.DataFrame(results)  
scores_df.to_csv(output_scores_filename, index=False)

print(f"\nDataset info:")
print(f"Total traffic points: {len(iat)}")
print(f"Window size: {windowsize}")
print(f"Number of windows: {len(results[eps[0]])}") 

print("\nSummary statistics (Original ε-similarity):")
for epsilon in eps:
    values = results[epsilon]  
    print(f"ε={epsilon}: min={min(values):.3f}, max={max(values):.3f}, "
          f"mean={np.mean(values):.3f}, median={np.median(values):.3f}, "
          f"std={np.std(values):.3f}")