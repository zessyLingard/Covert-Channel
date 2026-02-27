import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import RocCurveDisplay

# --- Configuration ---
LEGIT_FILE = "data/past_data/legit_traffic_seconds.csv"
COVERT_FILE = "data/no_vpn_fuzzy.csv"
WINDOW_SIZE = 510
EPSILONS = [0.005, 0.008, 0.01, 0.02, 0.03, 0.1]

# --- Analysis Functions ---
def process_traffic_file(iat_series):
    """Calculates ε-similarity scores for a file"""
    scores_by_eps = {e: [] for e in EPSILONS}
    num_full_windows = len(iat_series) // WINDOW_SIZE
    for i in range(num_full_windows):
        window = iat_series.iloc[i*WINDOW_SIZE : (i+1)*WINDOW_SIZE].sort_values(ignore_index=True)
        # Vectorized calculation for speed
        diffs = np.abs(window.diff().iloc[1:])
        ratios = diffs / (window.iloc[:-1] + 1e-9).values
        for e in EPSILONS:
            scores_by_eps[e].append(np.sum(ratios < e) / len(ratios))
    return scores_by_eps

def get_labels_scores(legit_scores, covert_scores, epsilon):
    """Get labels and scores for a specific epsilon"""
    l = np.array(legit_scores[epsilon])
    c = np.array(covert_scores[epsilon])
    if len(l) == 0 or len(c) == 0:
        return None, None
    y = np.concatenate([np.zeros(len(l)), np.ones(len(c))])
    scores = np.concatenate([l, c])
    if len(np.unique(y)) < 2:
        return None, None
    return y, scores

# --- Main Logic ---
if __name__ == "__main__":
    print("="*60)
    print("ε-Similarity Detection: Comparing Legit vs Covert Traffic")
    print("="*60)
    
    # Load data
    print(f"\nLoading covert traffic from '{COVERT_FILE}'...")
    try:
        covert_iat = pd.to_numeric(pd.read_csv(COVERT_FILE).iloc[:,0], errors='coerce').dropna()
        print(f"  → {len(covert_iat):,} inter-arrival times loaded")
    except Exception as e:
        print(f"Error loading covert data: {e}")
        exit()
    
    n_covert = len(covert_iat)
    print(f"\nLoading legitimate traffic from '{LEGIT_FILE}' (limited to {n_covert:,} samples)...")
    try:
        legit_iat = pd.to_numeric(pd.read_csv(LEGIT_FILE, encoding='utf-16').iloc[:,0], errors='coerce').dropna().iloc[:n_covert].reset_index(drop=True)
        print(f"  → {len(legit_iat):,} inter-arrival times loaded")
    except Exception as e:
        print(f"Error loading legit data: {e}")
        exit()
    
    # Process traffic
    print(f"\nProcessing with window size = {WINDOW_SIZE}...")
    legit_scores = process_traffic_file(legit_iat)
    covert_scores = process_traffic_file(covert_iat)
    
    print(f"  → Legit windows: {len(legit_scores[EPSILONS[0]])}")
    print(f"  → Covert windows: {len(covert_scores[EPSILONS[0]])}")
    
    # Calculate AUC for each epsilon
    print("\n" + "="*60)
    print("RESULTS: AUC for each eps value")
    print("="*60)
    print(f"{'eps':<10} {'AUC':<10} {'Interpretation'}")
    print("-"*60)
    
    n = len(EPSILONS)
    cols = min(3, n)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(4.5 * cols, 4 * rows))
    axes = np.array(axes).flatten()
    
    for i, e in enumerate(EPSILONS):
        ax = axes[i]
        y, scores = get_labels_scores(legit_scores, covert_scores, e)
        if y is not None:
            display = RocCurveDisplay.from_predictions(y, scores, ax=ax,
                                                       color='blue', lw=1.5, name=None)
            auc_val = display.roc_auc
            ax.plot([0, 1], [0, 1], 'r--', lw=1)
            ax.legend([f'AUC = {auc_val:.2f}'], loc='lower right', fontsize=9,
                      frameon=False)
        ax.set_title(f'ε = {e}', fontsize=11)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.set_xlabel('False Positive Rate', fontsize=9)
        ax.set_ylabel('True Positive Rate', fontsize=9)
        ax.tick_params(labelsize=8)
    
    # Hide unused subplots
    for j in range(n, len(axes)):
        axes[j].set_visible(False)
    
    plt.tight_layout()
    plt.savefig("roc_auc_result.png", dpi=300, bbox_inches='tight')
    print("Plot saved as 'roc_auc_result.png'")
    plt.show()