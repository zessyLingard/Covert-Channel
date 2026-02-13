import pandas as pd
import numpy as np
import os

# --- Configuration ---
WINDOW_SIZE = 2000
EPSILONS = [0.005, 0.008, 0.01, 0.02, 0.03, 0.1]

def calculate_esimilarity_mean(x):
    if len(x) < 2: return {e: 0.0 for e in EPSILONS}
    denominator = x.sort_values(ignore_index=True)
    # Calculate relative difference between sorted neighbors
    lambdas = (denominator.rolling(2)
               .apply(lambda y: abs(y.iloc[0] - y.iloc[1]) / (y.iloc[0] + 1e-9))
               .dropna())
    
    res = {}
    for e in EPSILONS:
        if lambdas.empty: res[e] = 0.0
        else: res[e] = np.count_nonzero(lambdas < e) / lambdas.count()
    return res

def get_file_scores(filepath, encoding='utf-8'):
    try:
        # Try reading with provided encoding, fallback to default if needed
        try:
            df = pd.read_csv(filepath, encoding=encoding)
        except:
            df = pd.read_csv(filepath) # Try default encoding
            
        # Attempt to find the time column (looking for 'Time', 'IAT', or first column)
        if "Time" in df.columns:
            col_data = df["Time"]
        elif "IAT" in df.columns:
            col_data = df["IAT"]
        else:
            col_data = df.iloc[:, 0]

        iat = pd.to_numeric(col_data, errors='coerce').dropna()
        
        scores_by_eps = {e: [] for e in EPSILONS}
        
        # --- FIX FOR SHORT FILES ---
        total_packets = len(iat)
        
        if total_packets < WINDOW_SIZE:
            print(f"Notice: '{os.path.basename(filepath)}' is short ({total_packets} pkts). Processing as 1 window.")
            # Treat the entire file as a single window
            w_scores = calculate_esimilarity_mean(iat)
            for e in EPSILONS:
                scores_by_eps[e].append(w_scores[e])
        else:
            # Standard processing
            num_windows = total_packets // WINDOW_SIZE
            print(f"Processing {os.path.basename(filepath)} ({num_windows} windows)...")
            
            for i in range(num_windows):
                window = iat.iloc[i*WINDOW_SIZE : (i+1)*WINDOW_SIZE]
                w_scores = calculate_esimilarity_mean(window)
                for e in EPSILONS:
                    scores_by_eps[e].append(w_scores[e])
                
        # Calculate Mean score for the whole file
        means = {e: np.mean(scores_by_eps[e]) for e in EPSILONS}
        return means
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

# --- Main Execution ---

if __name__ == "__main__":
    print("--- DIAGNOSTIC: SCORE ANALYSIS (Short File Support) ---")
    
    # 1. Analyze Legitimate Traffic (Baseline)
    # Using utf-16 because your previous logs suggested it for legit files
    legit_means = get_file_scores("data/legit_traffic_seconds.csv", "utf-16")
    
    # 2. Analyze Your Custom Short File
    # Warning: Ensure the filename matches exactly what is in your folder
    fuzzed_means = get_file_scores("covert_ipd.csv", "utf-8") 

    # 3. Print Comparison Table
    print("\n" + "="*65)
    print(f"{'Epsilon (ε)':<15} | {'Legit Score':<15} | {'Custom Score':<15} | {'Gap'}")
    print("="*65)
    
    if legit_means and fuzzed_means:
        for e in EPSILONS:
            l_score = legit_means[e]
            f_score = fuzzed_means[e]
            gap = abs(l_score - f_score)
            
            # Visual marker for large gaps
            gap_str = f"{gap:.4f}"
            if gap > 0.3: gap_str += " (DETECTABLE)"
            
            print(f"{e:<15} | {l_score:.4f}          | {f_score:.4f}          | {gap_str}")
    else:
        print("Could not compare due to file errors.")