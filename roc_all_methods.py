import pandas as pd
import numpy as np
import math
import gzip
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

# ============================================================
# CONFIGURATION
# ============================================================
LEGIT_FILE = "data/http.csv"
COVERT_FILE = "data/no_vpn_fuzz.csv"
WINDOW_SIZE = 500
EPSILONS = [0.005, 0.008, 0.01, 0.02, 0.03, 0.1]
EPSILON_TO_PLOT = 0.01  # epsilon used for the ROC subplots

# ============================================================
# DETECTION METHOD 1: Original ε-Similarity
# ============================================================
def eps_similarity(window, epsilons=EPSILONS):
    """Calculate ε-similarity scores for a window of IATs."""
    if len(window) < 2:
        return {e: 0.0 for e in epsilons}
    sorted_w = window.sort_values(ignore_index=True)
    diffs = np.abs(sorted_w.diff().iloc[1:])
    ratios = diffs / (sorted_w.iloc[:-1].values + 1e-9)
    return {e: float(np.sum(ratios < e) / len(ratios)) for e in epsilons}

# ============================================================
# DETECTION METHOD 2: Enhanced ε-Similarity (top 1/3)
# ============================================================
def enhanced_eps_similarity(window, epsilons=EPSILONS):
    """Calculate enhanced ε-similarity using only the top 1/3 of sorted values."""
    if len(window) < 3:
        return {e: 0.0 for e in epsilons}
    sorted_w = window.sort_values(ignore_index=True)
    top_third = sorted_w[math.floor(len(sorted_w) * (2 / 3)):]
    return eps_similarity(top_third, epsilons)

# ============================================================
# DETECTION METHOD 3: Compressibility
# ============================================================
def iat2str(i):
    """Convert an IAT value to a compact string representation."""
    if i == 0:
        return '0'
    try:
        i = round(i, 2 - int(math.floor(math.log10(abs(i)))) - 1)
    except ValueError:
        return ""
    s = '{:.16f}'.format(i).split('.')[1]
    leading_zeros = len(s) - len(s.lstrip('0'))
    if leading_zeros == 0:
        return s.strip('0')
    else:
        return chr(64 + leading_zeros) + s.strip('0')


def compressibility(window):
    """Calculate compression ratio (original / compressed) for a window."""
    full_string = window.apply(iat2str).str.cat()
    if not full_string:
        return np.nan
    original_size = len(full_string.encode())
    compressed_size = len(gzip.compress(full_string.encode()))
    if compressed_size == 0:
        return np.nan
    return original_size / compressed_size

# ============================================================
# PROCESSING HELPERS
# ============================================================
def process_eps_windows(iat_series, detection_fn, label):
    """Run an ε-based detector over all windows, return dict of score lists per epsilon."""
    scores_by_eps = {e: [] for e in EPSILONS}
    num_windows = len(iat_series) // WINDOW_SIZE
    for i in range(num_windows):
        window = iat_series.iloc[i * WINDOW_SIZE: (i + 1) * WINDOW_SIZE]
        score_dict = detection_fn(window)
        for e in EPSILONS:
            scores_by_eps[e].append(score_dict[e])
    print(f"  [{label}] {num_windows} windows processed")
    return scores_by_eps


def process_compress_windows(iat_series, label):
    """Run compressibility detector over all windows, return array of scores."""
    scores = (
        iat_series
        .groupby(np.arange(len(iat_series)) // WINDOW_SIZE)
        .apply(compressibility)
        .dropna()
    )
    print(f"  [{label}] {len(scores)} windows processed")
    return scores.to_numpy()


def compute_roc(legit_scores, covert_scores):
    """Compute ROC curve and AUC from legit/covert score arrays."""
    all_scores = np.concatenate([legit_scores, covert_scores])
    labels = np.concatenate([np.zeros(len(legit_scores)), np.ones(len(covert_scores))])
    if len(np.unique(labels)) < 2:
        return np.nan, None, None
    fpr, tpr, _ = roc_curve(labels, all_scores)
    return auc(fpr, tpr), fpr, tpr

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Unified Covert Channel Detection — ROC AUC Analysis")
    print("=" * 60)

    # --- Load data ---
    def load_csv(path):
        """Try UTF-8 first, fall back to UTF-16."""
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.read_csv(path, encoding='utf-16')

    print(f"\nLoading legitimate traffic from '{LEGIT_FILE}'...")
    legit_iat = pd.to_numeric(load_csv(LEGIT_FILE).iloc[:, 0], errors='coerce').dropna()
    print(f"  → {len(legit_iat):,} IATs loaded")

    print(f"Loading covert traffic from '{COVERT_FILE}'...")
    covert_iat = pd.to_numeric(load_csv(COVERT_FILE).iloc[:, 0], errors='coerce').dropna()
    print(f"  → {len(covert_iat):,} IATs loaded")

    # --- Method 1: Original ε-similarity ---
    print(f"\n--- Method 1: Original ε-Similarity (window={WINDOW_SIZE}) ---")
    legit_eps_orig = process_eps_windows(legit_iat, eps_similarity, "Legit")
    covert_eps_orig = process_eps_windows(covert_iat, eps_similarity, "Covert")

    # --- Method 2: Enhanced ε-similarity ---
    print(f"\n--- Method 2: Enhanced ε-Similarity (top 1/3, window={WINDOW_SIZE}) ---")
    legit_eps_enh = process_eps_windows(legit_iat, enhanced_eps_similarity, "Legit")
    covert_eps_enh = process_eps_windows(covert_iat, enhanced_eps_similarity, "Covert")

    # --- Method 3: Compressibility ---
    print(f"\n--- Method 3: Compressibility (window={WINDOW_SIZE}) ---")
    legit_comp = process_compress_windows(legit_iat, "Legit")
    covert_comp = process_compress_windows(covert_iat, "Covert")

    # ========================================================
    # RESULTS TABLE
    # ========================================================
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)

    # ε-similarity results for each epsilon
    eps_results_orig = {}
    eps_results_enh = {}
    print(f"\n{'Method':<28} {'ε':<10} {'AUC':<10}")
    print("-" * 50)
    for e in EPSILONS:
        auc_o, fpr_o, tpr_o = compute_roc(
            np.array(legit_eps_orig[e]), np.array(covert_eps_orig[e])
        )
        eps_results_orig[e] = (auc_o, fpr_o, tpr_o)

        auc_e, fpr_e, tpr_e = compute_roc(
            np.array(legit_eps_enh[e]), np.array(covert_eps_enh[e])
        )
        eps_results_enh[e] = (auc_e, fpr_e, tpr_e)

        print(f"{'Original ε-sim':<28} {e:<10} {auc_o:.4f}")
        print(f"{'Enhanced ε-sim (top 1/3)':<28} {e:<10} {auc_e:.4f}")

    auc_c, fpr_c, tpr_c = compute_roc(legit_comp, covert_comp)
    print(f"\n{'Compressibility':<28} {'—':<10} {auc_c:.4f}")

    # ========================================================
    # PLOTTING — 3 subplots
    # ========================================================
    print("\nGenerating combined ROC plot...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # (a) Original ε-similarity
    ax = axes[0]
    auc_o, fpr_o, tpr_o = eps_results_orig[EPSILON_TO_PLOT]
    if fpr_o is not None:
        ax.plot(fpr_o, tpr_o, color='blue', lw=2, label=f'Covert (AUC={auc_o:.2f})')
    ax.plot([0, 1], [0, 1], 'r--', lw=1.5, label='Random')
    ax.set_title(f'(a) Original ε-Similarity (ε={EPSILON_TO_PLOT})')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)

    # (b) Enhanced ε-similarity
    ax = axes[1]
    auc_e, fpr_e, tpr_e = eps_results_enh[EPSILON_TO_PLOT]
    if fpr_e is not None:
        ax.plot(fpr_e, tpr_e, color='green', lw=2, label=f'Covert (AUC={auc_e:.2f})')
    ax.plot([0, 1], [0, 1], 'r--', lw=1.5, label='Random')
    ax.set_title(f'(b) Enhanced ε-Similarity (ε={EPSILON_TO_PLOT})')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)

    # (c) Compressibility
    ax = axes[2]
    if fpr_c is not None:
        ax.plot(fpr_c, tpr_c, color='orange', lw=2, label=f'Covert (AUC={auc_c:.2f})')
    ax.plot([0, 1], [0, 1], 'r--', lw=1.5, label='Random')
    ax.set_title('(c) Compressibility')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)

    plt.suptitle(
        f'Covert Channel Detectability — {LEGIT_FILE} vs {COVERT_FILE}',
        fontsize=14, fontweight='bold'
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig("roc_all_methods.png", dpi=300, bbox_inches='tight')
    print("Plot saved as 'roc_all_methods.png'")
    plt.show()

    print("\nDone.")
