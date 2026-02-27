#!/usr/bin/env python3
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.switch_backend("Agg")


def analyze(filename):
    print(f"\nLoading file: {filename}\n")

    df = pd.read_csv(filename, header=None, encoding = "utf-16")
    col = df.columns[0]

    iat = pd.to_numeric(df[col], errors="coerce").dropna()

    print("=== BASIC STATS ===")
    print(iat.describe())

    total = len(iat)
    zeros = np.sum(iat == 0)
    pct_zero = (zeros / total) * 100

    print("\n=== ZERO ANALYSIS ===")
    print(f"Total samples: {total}")
    print(f"Zero values : {zeros}")
    print(f"Zero %      : {pct_zero:.2f}%")

    print("\n=== SMALL VALUE DISTRIBUTION ===")
    print(f"IAT < 1ms   : {(np.sum(iat < 0.001)/total)*100:.2f}%")
    print(f"IAT < 5ms   : {(np.sum(iat < 0.005)/total)*100:.2f}%")
    print(f"IAT < 10ms  : {(np.sum(iat < 0.01)/total)*100:.2f}%")

    print("\n=== TOP 20 MOST FREQUENT VALUES ===")
    print(iat.value_counts().head(20))

    # Histogram full range
    plt.figure(figsize=(10, 6))
    plt.hist(iat, bins=100)
    plt.title("IAT Histogram (Full Range)")
    plt.xlabel("IAT (seconds)")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("hist_full.png", dpi=300)
    print("\nSaved: hist_full.png")

    # Histogram zoomed into small region
    plt.figure(figsize=(10, 6))
    plt.hist(iat[iat < 0.05], bins=100)
    plt.title("IAT Histogram (Zoom < 50ms)")
    plt.xlabel("IAT (seconds)")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("hist_zoom_50ms.png", dpi=300)
    print("Saved: hist_zoom_50ms.png")

    print("\n=== QUICK HEALTH CHECK ===")

    if pct_zero > 50:
        print("⚠ WARNING: Extremely high zero percentage. Likely capture artifact.")
    elif pct_zero > 20:
        print("⚠ High zero percentage. Possibly burst batching.")
    else:
        print("✓ Zero percentage looks reasonable.")

    if np.median(iat) < 0.00001:
        print("⚠ Median extremely small → likely NIC offloading issue.")
    else:
        print("✓ Median looks reasonable.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <iat_csv_file>")
        sys.exit(1)

    analyze(sys.argv[1])