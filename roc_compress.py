import pandas as pd
import numpy as np
import math
import gzip
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

# --- CẤU HÌNH ---
LEGIT_FILE = "data/http.csv"
COVERT_FILE = "data/.csv"
WINDOW_SIZE = 2000

def iat2str(i):
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

def compress(x):
    """Calculate compression ratio for a window of IAT values"""
    mystring = x.apply(iat2str)
    full_string = mystring.str.cat()
    if not full_string:
        return np.nan
    original_size = len(full_string.encode())
    compressed_size = len(gzip.compress(full_string.encode()))
    if compressed_size == 0:
        return np.nan
    return original_size / compressed_size

# This is the missing function!
def calculate_compressibility_score(window):
    """Calculate compressibility score for a single window"""
    return compress(window)

# --- HÀM XỬ LÝ DỮ LIỆU CHÍNH ---
def run_analysis(iat_series):
    print(f"Calculating compressibility scores for {len(iat_series)} IATs...")
    scores = iat_series.groupby(np.arange(len(iat_series)) // WINDOW_SIZE).apply(calculate_compressibility_score).dropna()
    print(f"Processed {len(scores)} full windows.")
    return scores.to_numpy()

# --- LOGIC THỰC THI CHÍNH ---
try:
    print("Loading legitimate traffic...")
    legit_df = pd.read_csv(LEGIT_FILE, encoding='utf-8')
    legit_iat = pd.to_numeric(legit_df.iloc[:, 0], errors='coerce').dropna()
    # Step 2 from Cabuk et al.: drop all IATs over 1.0 sec
    legit_iat = legit_iat[legit_iat <= 1.0].reset_index(drop=True)
    legit_scores = run_analysis(legit_iat)

    print(f"\nLoading covert traffic from '{COVERT_FILE}'...")
    covert_df = pd.read_csv(COVERT_FILE)
    covert_iat = pd.to_numeric(covert_df.iloc[:, 0], errors='coerce').dropna()
    # Step 2 from Cabuk et al.: drop all IATs over 1.0 sec
    covert_iat = covert_iat[covert_iat <= 1.0].reset_index(drop=True)
    covert_scores = run_analysis(covert_iat)

except FileNotFoundError as e:
    print(f"\nError: File not found: {e}")
    exit()
except Exception as e:
    print(f"Error occurred: {e}")
    exit()

# --- TÍNH TOÁN AUC VÀ VẼ BIỂU ĐỒ ---
if len(legit_scores) > 0 and len(covert_scores) > 0:
    all_scores = np.concatenate([legit_scores, covert_scores])
    labels = np.concatenate([np.zeros(len(legit_scores)), np.ones(len(covert_scores))])
    
    fpr, tpr, _ = roc_curve(labels, all_scores)
    roc_auc = auc(fpr, tpr)

    print(f"\n--- Compressibility Score Results ---")
    print(f"Legitimate traffic - Mean: {np.mean(legit_scores):.4f}, Std: {np.std(legit_scores):.4f}")
    print(f"Covert traffic - Mean: {np.mean(covert_scores):.4f}, Std: {np.std(covert_scores):.4f}")
    print(f"AUC: {roc_auc:.4f}")

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='green', lw=2, label=f'ROC Curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Compressibility-based Detection: ROC Curve')
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("roc_compress_fuzzed.png", dpi=300, bbox_inches='tight')
    print("\nPlot saved as 'roc_compress_fuzzed.png'")
    plt.show()
else:
    print("\nNot enough data to calculate AUC.")