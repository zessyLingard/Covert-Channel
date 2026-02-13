import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc


LEGIT_FILE = "data/legit_traffic_seconds.csv"
COVERT_FILE = "data/fuzzy_o.csv" 

WINDOW_SIZE = 2000
EPSILONS = [0.005, 0.008, 0.01, 0.02, 0.03, 0.1]
epsilon_to_plot = 0.01

def fun_eps(x):
    """Calculate original ε-similarity score."""
    if len(x) < 2: 
        return {e: 0.0 for e in EPSILONS}
    lambdas = (x.sort_values(ignore_index=True)
               .rolling(2)
               .apply(lambda y: abs(y.iloc[0] - y.iloc[1]) / (y.iloc[0] + 1e-9))
               .dropna())
    res = {}
    for e in EPSILONS:
        res[e] = np.count_nonzero(lambdas < e) / lambdas.count() if not lambdas.empty else 0.0
    return res

def improved_eps(x):
    """Calculate enhanced ε-similarity score (using top 1/3 of sorted values)."""
    if len(x) < 3: 
        return {e: 0.0 for e in EPSILONS}
    newDat = x.sort_values(ignore_index=True)[math.floor(len(x)*(2/3)):]
    return fun_eps(newDat)

def run_analysis(iat_series, detection_function):
    print(f"Calculating scores for {len(iat_series)} IATs using '{detection_function.__name__}'...")
    scores_by_eps = {e: [] for e in EPSILONS}
    num_full_windows = len(iat_series) // WINDOW_SIZE
    for i in range(num_full_windows):
        window_data = iat_series.iloc[i*WINDOW_SIZE : (i+1)*WINDOW_SIZE]
        score_dict = detection_function(window_data)
        for e in EPSILONS:
            scores_by_eps[e].append(score_dict[e])
    print(f"Processed {num_full_windows} windows.")
    return scores_by_eps

try:
    # 1. Load all 3 datasets
    print("Loading legitimate traffic...")
    legit_df = pd.read_csv(LEGIT_FILE, encoding='utf-16')
    legit_iat = pd.to_numeric(legit_df.iloc[:, 0], errors='coerce').dropna()
    
    print("Loading covert traffic...")
    covert_df = pd.read_csv(COVERT_FILE)
    covert_iat = pd.to_numeric(covert_df.iloc[:, 0], errors='coerce').dropna()

    # 2. Run analysis with ORIGINAL detector
    print("\n--- Running Original Detector (fun_eps) ---")
    legit_scores_orig = run_analysis(legit_iat, fun_eps)
    covert_scores_orig = run_analysis(covert_iat, fun_eps)
    
    # 3. Run analysis with ENHANCED detector
    print("\n--- Running Enhanced Detector (improved_eps) ---")
    legit_scores_enh = run_analysis(legit_iat, improved_eps)
    covert_scores_enh = run_analysis(covert_iat, improved_eps)

except FileNotFoundError as e:
    print(f"\nError: File not found: {e}")
    print(f"Please ensure these files exist:")
    print(f"- {LEGIT_FILE}")
    print(f"- {COVERT_FILE}")
    exit()


def get_auc(legit_scores, covert_scores):
    """Calculate AUC and return FPR, TPR."""
    all_scores = np.concatenate([legit_scores, covert_scores])
    labels = np.concatenate([np.zeros(len(legit_scores)), np.ones(len(covert_scores))])
    fpr, tpr, _ = roc_curve(labels, all_scores)
    return auc(fpr, tpr), fpr, tpr

# Create figure with 2 subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# --- Plot (a): Original ε-similarity ---
legit_s_orig = np.array(legit_scores_orig[epsilon_to_plot])
covert_s_orig = np.array(covert_scores_orig[epsilon_to_plot])

auc_orig, fpr_orig, tpr_orig = get_auc(legit_s_orig, covert_s_orig)

print(f"\n--- Original Detector Results (ε={epsilon_to_plot}) ---")
print(f"Covert Channel AUC: {auc_orig:.4f}")

# Plot ROC curves
line_covert_orig, = ax1.plot(fpr_orig, tpr_orig, color='blue', lw=2, label=f'Covert (AUC = {auc_orig:.2f})')
ax1.plot([0, 1], [0, 1], color='red', lw=1.5, linestyle='--', label='Random')

ax1.legend(loc='lower right')
ax1.set_title('(a) Original ε-similarity')
ax1.set_xlabel('False Positive Rate')
ax1.set_ylabel('True Positive Rate')
ax1.grid(True)


# --- Plot (b): Enhanced ε-similarity ---
legit_s_enh = np.array(legit_scores_enh[epsilon_to_plot])
covert_s_enh = np.array(covert_scores_enh[epsilon_to_plot])

auc_enh, fpr_enh, tpr_enh = get_auc(legit_s_enh, covert_s_enh)

print(f"\n--- Enhanced Detector Results (ε={epsilon_to_plot}) ---")
print(f"Covert Channel AUC: {auc_enh:.4f}")

# Plot ROC curves
line_covert_enh, = ax2.plot(fpr_enh, tpr_enh, color='blue', lw=2, label=f'Covert (AUC = {auc_enh:.2f})')
ax2.plot([0, 1], [0, 1], color='red', lw=1.5, linestyle='--', label='Random')

ax2.legend(loc='lower right')
ax2.set_title('(b) Enhanced ε-similarity')
ax2.set_xlabel('False Positive Rate')
ax2.set_ylabel('True Positive Rate')
ax2.grid(True)

plt.suptitle('Covert Channel Detectability: http.csv vs fuzzy_o.csv', fontsize=14, fontweight='bold')
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("compare_enhanced.png", dpi=300, bbox_inches='tight')
print("\nPlot saved as 'compare_enhanced.png'")
plt.show()