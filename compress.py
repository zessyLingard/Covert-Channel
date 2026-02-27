import pandas as pd
import numpy as np
import math
import gzip
import matplotlib.pyplot as plt

np.random.seed(0)
windowsize = 512

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
    mystring = x.apply(iat2str)
    full_string = mystring.str.cat()
    if not full_string:
        return np.nan
    original_size = len(full_string.encode())
    compressed_size = len(gzip.compress(full_string.encode()))
    if compressed_size == 0:
        return np.nan
    return original_size / compressed_size

input_filename = "data/past_data/timings_1_fuzzed.csv"

try:
    input_df = pd.read_csv(input_filename, header=None)
    iats_seconds = pd.to_numeric(input_df.iloc[:, 0], errors='coerce').dropna()

    # Step 2 from Cabuk et al.: drop all IATs over 1.0 sec
    iats_seconds = iats_seconds[iats_seconds <= 1.0].reset_index(drop=True)

    if len(iats_seconds) >= windowsize:
        scores = iats_seconds.groupby(np.arange(len(iats_seconds)) // windowsize).apply(compress)
        scores = scores.dropna()

        print(scores.describe())

        # --- Plotting ---
        plt.figure(figsize=(4, 3))
        plt.hist(scores, bins=20, edgecolor='black')

        plt.xlim(0, 10)
        plt.ylim(0, 400)
        plt.xticks(np.arange(0, 11, 2))
        plt.yticks(np.arange(0, 451, 100))

        plt.xlabel('Compressibility Score')
        plt.ylabel('')
        plt.title('')
        plt.tight_layout()
        plt.text(0.5, -0.25, '(c) e-klibur', ha='center', va='center', transform=plt.gca().transAxes, fontsize=13)

        plt.savefig('compression_scores_covert_fuzzed.png', dpi=200, bbox_inches='tight')
        plt.show()

    else:
        print("\nERROR: Not enough data to form a single window.")

except FileNotFoundError:
    print(f"CRITICAL ERROR: The file '{input_filename}' was not found.")