import pandas as pd
import numpy as np
import os

np.random.seed(0)

def inject_fuzzy(x, tau):

    thresh = (3 * tau) / 2

    if x < thresh:
        # For small values: sample from truncated normal distribution
        res = np.abs(np.random.normal(0.0, scale=thresh / 7))
        while res > thresh:  # Keep resampling until within threshold
            res = np.abs(np.random.normal(0.0, scale=thresh / 7))
        return res
    else:
        # For larger values: uniform random choice from range
        return np.random.choice(np.arange(thresh, 2.4 * tau, 0.001))


if __name__ == "__main__":

    experiments = [
        {"tau_ms": 5,   "cleaned_file": "timings_1_cleaned.csv", "fuzzed_file": "timings_1_fuzzed.csv"},
        {"tau_ms": 10,  "cleaned_file": "timings_2_cleaned.csv", "fuzzed_file": "timings_2_fuzzed.csv"},
        {"tau_ms": 20,  "cleaned_file": "timings_3_cleaned.csv", "fuzzed_file": "timings_3_fuzzed.csv"},
        {"tau_ms": 30,  "cleaned_file": "timings_4_cleaned.csv", "fuzzed_file": "timings_4_fuzzed.csv"},
        {"tau_ms": 40,  "cleaned_file": "timings_5_cleaned.csv", "fuzzed_file": "timings_5_fuzzed.csv"},
        {"tau_ms": 50,  "cleaned_file": "timings_6_cleaned.csv", "fuzzed_file": "timings_6_fuzzed.csv"},
        {"tau_ms": 100, "cleaned_file": "timings_7_cleaned.csv", "fuzzed_file": "timings_7_fuzzed.csv"},
    ]

    print("--- Starting Fuzziness Injection (using Paper's Algorithm) ---\n")

    for exp in experiments:
        tau_seconds = exp["tau_ms"] / 1000.0
        input_file = exp["cleaned_file"]
        output_file = exp["fuzzed_file"]

        print(f"[+] Processing {input_file} with tau = {exp['tau_ms']}ms...")

        try:
            df = pd.read_csv(input_file)
            
            # Apply fuzzing to the Time/IAT column
            df["Time"] = df["Time"].apply(lambda x: inject_fuzzy(x, tau_seconds))
            
            df.to_csv(output_file, index=False)
            print(f"    -> Saved fuzzed data to {output_file}\n")

        except FileNotFoundError:
            print(f"    ERROR: Input file not found: {input_file}\n")
        except Exception as e:
            print(f"    An unexpected error occurred: {e}\n")

    print("--- All fuzziness injection tasks are complete. ---")