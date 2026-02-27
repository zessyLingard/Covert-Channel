import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import os

# ========================
# CẤU HÌNH (CONFIG)
# ========================
LEGIT_FILE = "data/legit_traffic_seconds.csv"  # File Legit (hoặc VPN) của bạn
COVERT_FILE = "data/no_vpn_fuzzy.csv" # File Covert fuzzed
WINDOW_SIZE = 510
EPSILONS = [0.005, 0.008, 0.01, 0.02, 0.03, 0.1]

# ========================
# THUẬT TOÁN ORIGINAL ε-SIMILARITY
# ========================
def fun_eps(x):
    """Tính điểm ε-similarity cho 1 cửa sổ (Original version)"""
    lambdas = (x.sort_values(ignore_index=True)
                 .rolling(2)
                 .apply(lambda y: abs(y.iloc[0] - y.iloc[1]) / y.iloc[0])
                 .dropna())
    res = {}
    total_count = lambdas.count()
    if total_count == 0:
        for e in EPSILONS:
            res[e] = np.nan
        return res
        
    for e in EPSILONS:
        res[e] = np.count_nonzero(lambdas < e) / total_count
    return res

# ========================
# HÀM XỬ LÝ CHIA CỬA SỔ
# ========================
def process_traffic(file_path, label_name, encoding='utf-8'):
    print(f"Loading {label_name} from {file_path}...")
    try:
        df = pd.read_csv(file_path, encoding=encoding)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='utf-16') 
        
    iat = pd.to_numeric(df.iloc[:, 0], errors='coerce').dropna().reset_index(drop=True)
    
    print(f"Total IATs: {len(iat)}")
    
    # Chia window
    grouped = iat.groupby(np.arange(len(iat)) // WINDOW_SIZE)
    
    results = {e: [] for e in EPSILONS}
    for _, group_data in grouped:
        if len(group_data) < 2: # Bỏ qua nếu cửa sổ quá nhỏ không tính được lambda
            continue
            
        score_dict = fun_eps(group_data)
        for e in EPSILONS:
            if pd.notna(score_dict[e]):
                results[e].append(score_dict[e])
                
    print(f"Generated {len(results[EPSILONS[0]])} valid windows for {label_name}.")
    return results

# ========================
# THỰC THI CHÍNH
# ========================
def main():
    legit_scores_dict = process_traffic(LEGIT_FILE, "Legitimate Traffic", encoding='utf-16')
    covert_scores_dict = process_traffic(COVERT_FILE, "Covert Traffic")
    
    n_legit = len(legit_scores_dict[EPSILONS[0]])
    n_covert = len(covert_scores_dict[EPSILONS[0]])
    
    if n_legit == 0 or n_covert == 0:
        print("\n[!] Lỗi: Không đủ cửa sổ dữ liệu để tính ROC/AUC.")
        return

    print("\n" + "="*40)
    print(" KẾT QUẢ AUC CHO TỪNG NGƯỠNG ε")
    print("="*40)

    # Chuẩn bị gán nhãn (Legit = 0, Covert = 1)
    labels = np.concatenate([np.zeros(n_legit), np.ones(n_covert)])
    
    plt.figure(figsize=(10, 8))
    
    # Tính AUC và vẽ ROC cho TỪNG mức epsilon
    for e in EPSILONS:
        l_scores = np.array(legit_scores_dict[e])
        c_scores = np.array(covert_scores_dict[e])
        all_scores = np.concatenate([l_scores, c_scores])
        
        fpr, tpr, _ = roc_curve(labels, all_scores)
        roc_auc = auc(fpr, tpr)
        
        # Xử lý lật nhãn nếu thuật toán tàng hình làm giảm điểm số
        if roc_auc < 0.5:
            fpr, tpr, _ = roc_curve(labels, -all_scores)
            roc_auc = auc(fpr, tpr)
            
        print(f"ε = {e:<6} | AUC = {roc_auc:.4f}")
        
        # Vẽ đường ROC cho mức epsilon này
        plt.plot(fpr, tpr, lw=2, label=f'ε={e} (AUC = {roc_auc:.3f})')

    # Hoàn thiện biểu đồ ROC
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Guess')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate (Nhận nhầm Legit)')
    plt.ylabel('True Positive Rate (Bắt trúng Covert)')
    plt.title(f'ε-Similarity Detection ROC Curves\n(Window: {WINDOW_SIZE} | Legit: {n_legit} w. | Covert: {n_covert} w.)')
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_filename = "roc_epssim_original.png"
    plt.savefig(output_filename, dpi=300)
    print(f"\n[+] Đã lưu biểu đồ ROC gom chung tại: {output_filename}")
    plt.show()

if __name__ == "__main__":
    main()