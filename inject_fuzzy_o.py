import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import itertools
import random
import math

np.random.seed(0)

# The inject_fuzzy function expects the original delay x and the covert channel configuration tau and returns the modified delay

def inject_fuzzy(x, tau):
    thresh = (3*tau)/2

    if x < thresh:
        res = np.abs(np.random.normal(0.0,scale=thresh/7))
        while res > thresh:
            res = np.abs(np.random.normal(0.0,scale=thresh/7))
        return res
    else:
        return np.random.choice(np.append(np.arange(thresh+0.001,2.4*tau,0.001),[(10*tau)]))


# Example Usage

# Set tau corresponding to covert channel configuration
tau = 100 / 1000
# Read CSV
input = pd.read_csv("data/timings_7_cleaned.csv")

# Get IATs (first column is Time)
iat_cov = input["Time"]

# Inject fuzziness (using apply instead of parallel_apply for Windows)
iat_fuzz = iat_cov.apply(lambda x: inject_fuzzy(x, tau))

# Save to CSV
output_df = pd.DataFrame(iat_fuzz, columns=["Time"])
output_df.to_csv("data/fuzzy_o.csv", index=False)

