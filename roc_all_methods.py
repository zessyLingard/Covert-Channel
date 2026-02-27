import pandas as pd
import numpy as np
import gzip
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

# ============================================================
# CONFIGURATION
# ============================================================
LEGIT_FILE = "data/http.csv"
COVERT_FILE = "data/no_vpn_fuzzy.csv"

TARGET_PACKET_COUNT = 51000
WINDOW_SIZE = 510
EPSILON_TO_PLOT = 0.005

# ============================================================
# HELPER: DISJOINT CHUNKER (No Stride, Just Reshape)
# ============================================================
def get_disjoint_windows(data, window_size):
    """
    Splits data into clean, non-overlapping chunks.
    Drops any 'remainder' packets at the end to ensure perfect shapes.
    """
    # 1. Calculate how many full windows fit
    num_windows = len(data) // window_size
    
    # 2. Cut the data to the exact length needed
    cutoff = num_windows * window_size
    clean_data = data[:cutoff]
    
    # 3. Reshape into (Num_Windows, Window_Size)
    # This effectively removes "stride" by making it implicit (Stride = Size)
    return clean_data.reshape(num_windows, window_size)

# ============================================================
# 1. ORIGINAL ε-SIMILARITY
# ============================================================
def calc_eps_similarity(window, epsilon=0.01):
    if len(window) < 2: return 0.0
    sorted_w = np.sort(window)
    diffs = np.diff(sorted_w)
    denominators = sorted_w[1:] + 1e-12
    ratios = diffs / denominators
    score = np.sum(ratios < epsilon) / len(ratios)
    return score

# ============================================================
# 2. ENHANCED ε-SIMILARITY (The Remedy)
# ============================================================
def calc_enhanced_eps_similarity(window, epsilon=0.01):
    # 1. Sort ENTIRE window
    sorted_w = np.sort(window)

    # 2. Split (Top 33%)
    # For 510 size, this takes the last 170 packets
    third_idx = (len(sorted_w) * 2) // 3
    sub_window_3 = sorted_w[third_idx:]

    # 3. Calculate Score on Sub-window
    if len(sub_window_3) < 2: return 0.0
    diffs = np.diff(sub_window_3)
    denominators = sub_window_3[1:] + 1e-12
    ratios = diffs / denominators
    score = np.sum(ratios < epsilon) / len(ratios)
    return score

# ============================================================
# 3. COMPRESSIBILITY SCORE
# ============================================================
def calc_compressibility(window):
    # Convert to string (5 decimals)
    raw_bytes = " ".join([f"{x:.5f}" for x in window]).encode('utf-8')
    compressed_bytes = gzip.compress(raw_bytes)

    # Return raw ratio. We will negate it later for ROC.
    return len(compressed_bytes) / len(raw_bytes)

# ============================================================
# MAIN EXECUTION
# ============================================================
def run_evaluation():
    print("Loading data...")
    try:
        legit_full = pd.read_csv(LEGIT_FILE, encoding='utf-8')['IPDs'].dropna().values
    except (KeyError, ValueError):
        # Fallback if no header
        legit_full = pd.read_csv(LEGIT_FILE, header=None).values.flatten()

    try:
        covert_full = pd.read_csv(COVERT_FILE)['IPDs'].dropna().values
    except (KeyError, ValueError):
        covert_full = pd.read_csv(COVERT_FILE, header=None).values.flatten()

    # ---- STRICT DATA TRUNCATION ----
    print(f"Raw Legit Size: {len(legit_full)}")
    print(f"Raw Covert Size: {len(covert_full)}")

    # Force cut to TARGET_PACKET_COUNT (51,000)
    # If one file is smaller, we limit to the smaller size to be fair
    limit = min(TARGET_PACKET_COUNT, len(legit_full), len(covert_full))
    print(f"TRUNCATING DATA TO: {limit} packets.")

    legit_df = legit_full[:limit]
    covert_df = covert_full[:limit]

    # ---- GENERATE CLEAN WINDOWS ----
    legit_windows = get_disjoint_windows(legit_df, WINDOW_SIZE)
    covert_windows = get_disjoint_windows(covert_df, WINDOW_SIZE)

    print(f"Legit Samples: {len(legit_windows)}")
    print(f"Covert Samples: {len(covert_windows)}")

    # ---- CALCULATE SCORES ----
    print("Calculating scores...")

    # Labels: 0 = Legit, 1 = Covert
    y_true = [0] * len(legit_windows) + [1] * len(covert_windows)

    # 1. Original Epsilon
    scores_legit_eps = [calc_eps_similarity(w, EPSILON_TO_PLOT) for w in legit_windows]
    scores_covert_eps = [calc_eps_similarity(w, EPSILON_TO_PLOT) for w in covert_windows]
    y_scores_eps = scores_legit_eps + scores_covert_eps

    # 2. Enhanced Epsilon
    scores_legit_enh = [calc_enhanced_eps_similarity(w, EPSILON_TO_PLOT) for w in legit_windows]
    scores_covert_enh = [calc_enhanced_eps_similarity(w, EPSILON_TO_PLOT) for w in covert_windows]
    y_scores_enh = scores_legit_enh + scores_covert_enh

    # 3. Compressibility (Negated Ratio)
    scores_legit_comp = [calc_compressibility(w) for w in legit_windows]
    scores_covert_comp = [calc_compressibility(w) for w in covert_windows]
    y_scores_comp = [-s for s in scores_legit_comp] + [-s for s in scores_covert_comp]

    # ---- PLOTTING ----
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Plot 1
    fpr, tpr, _ = roc_curve(y_true, y_scores_eps)
    roc_auc = auc(fpr, tpr)
    axes[0].plot(fpr, tpr, color='blue', lw=2, label=f'AUC = {roc_auc:.2f}')
    axes[0].plot([0, 1], [0, 1], 'r--')
    axes[0].set_title(f'Original ε-Similarity (ε={EPSILON_TO_PLOT})')
    axes[0].set_xlabel('False Positive Rate')
    axes[0].set_ylabel('True Positive Rate')
    axes[0].legend(loc="lower right")

    # Plot 2
    fpr, tpr, _ = roc_curve(y_true, y_scores_enh)
    roc_auc = auc(fpr, tpr)
    axes[1].plot(fpr, tpr, color='green', lw=2, label=f'AUC = {roc_auc:.2f}')
    axes[1].plot([0, 1], [0, 1], 'r--')
    axes[1].set_title(f'Enhanced ε-Similarity (ε={EPSILON_TO_PLOT})')
    axes[1].set_xlabel('False Positive Rate')
    axes[1].set_ylabel('True Positive Rate')
    axes[1].legend(loc="lower right")

    # Plot 3
    fpr, tpr, _ = roc_curve(y_true, y_scores_comp)
    roc_auc = auc(fpr, tpr)
    axes[2].plot(fpr, tpr, color='orange', lw=2, label=f'AUC = {roc_auc:.2f}')
    axes[2].plot([0, 1], [0, 1], 'r--')
    axes[2].set_title('Compressibility (Negated)')
    axes[2].set_xlabel('False Positive Rate')
    axes[2].set_ylabel('True Positive Rate')
    axes[2].legend(loc="lower right")

    plt.tight_layout()
    plt.savefig("experiment_results_clean.png")
    print("Done! Saved plot to experiment_results_clean.png")

if __name__ == "__main__":
    run_evaluation()