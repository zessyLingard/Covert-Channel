import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

# --- Configuration ---
LEGIT_FILE = "data/legit_traffic_seconds.csv"
COVERT_FILE = "data/fuzzy_o.csv"
WINDOW_SIZE = 2000
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

def get_auc(legit_scores, covert_scores, epsilon):
    """Calculate AUC for a specific epsilon"""
    l = np.array(legit_scores[epsilon])
    c = np.array(covert_scores[epsilon])
    if len(l) == 0 or len(c) == 0:
        return np.nan, None, None
    y = np.concatenate([np.zeros(len(l)), np.ones(len(c))])
    scores = np.concatenate([l, c])
    if len(np.unique(y)) < 2:
        return np.nan, None, None
    fpr, tpr, _ = roc_curve(y, scores)
    return auc(fpr, tpr), fpr, tpr

# --- Main Logic ---
if __name__ == "__main__":
    print("="*60)
    print("ε-Similarity Detection: Comparing Legit vs Covert Traffic")
    print("="*60)
    
    # Load data
    print(f"\nLoading legitimate traffic from '{LEGIT_FILE}'...")
    try:
        legit_iat = pd.to_numeric(pd.read_csv(LEGIT_FILE, encoding='utf-16').iloc[:,0], errors='coerce').dropna()
        print(f"  → {len(legit_iat):,} inter-arrival times loaded")
    except Exception as e:
        print(f"Error loading legit data: {e}")
        exit()
    
    print(f"\nLoading covert traffic from '{COVERT_FILE}'...")
    try:
        covert_iat = pd.to_numeric(pd.read_csv(COVERT_FILE).iloc[:,0], errors='coerce').dropna()
        print(f"  → {len(covert_iat):,} inter-arrival times loaded")
    except Exception as e:
        print(f"Error loading covert data: {e}")
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
    
    results = {}
    for e in EPSILONS:
        auc_val, fpr, tpr = get_auc(legit_scores, covert_scores, e)
        results[e] = (auc_val, fpr, tpr)
        
        # Interpretation
        if np.isnan(auc_val):
            interp = "N/A"
        elif auc_val >= 0.9:
            interp = "Easily Detected! (Bad stealth)"
        elif auc_val >= 0.7:
            interp = "Somewhat Detectable"
        elif auc_val >= 0.6:
            interp = "Marginally Detectable"
        elif auc_val >= 0.4:
            interp = "Near Random (Good stealth)"
        else:
            interp = "Inverse Detection (Unusual)"
        
        print(f"{e:<10} {auc_val:.4f}     {interp}")
    
    # Plot ROC curves for all epsilons
    print("\nGenerating ROC plot...")
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(EPSILONS)))
    for i, e in enumerate(EPSILONS):
        auc_val, fpr, tpr = results[e]
        if fpr is not None and tpr is not None:
            ax.plot(fpr, tpr, color=colors[i], lw=2, label=f'ε={e} (AUC={auc_val:.2f})')
    
    ax.plot([0, 1], [0, 1], 'r--', lw=2, label='Random Classifier')
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title('ε-Similarity Detection: ROC Curves\n(http.csv vs fuzzy_o.csv)', fontsize=14)
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("roc_auc_result.png", dpi=300, bbox_inches='tight')
    print("Plot saved as 'roc_auc_result.png'")
    plt.show()