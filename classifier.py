import pandas as pd
import os

def clean_iat_data(input_filepath, output_filepath, tau_ms):
    target_0 = float(tau_ms)
    target_1 = float(tau_ms * 2)
    threshold = (target_0 + target_1) / 2.0

    try:
        df = pd.read_csv(input_filepath, header=0)
        raw_iats = pd.to_numeric(df['Time'], errors='coerce')
        raw_iats = raw_iats.dropna()

        def classify_to_target(iat):
            if iat <= threshold:
                return target_0
            else:
                return target_1

        cleaned_iats = raw_iats.apply(classify_to_target)
        cleaned_iats_seconds = cleaned_iats / 1000
        # Add 'Time' as the column header, keeping all valid data
        pd.DataFrame(cleaned_iats_seconds, columns=['Time']).to_csv(output_filepath, index=False)
        print(f"Successfully saved cleaned data (in seconds) to {os.path.basename(output_filepath)}\n")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_filepath}\n")

if __name__ == '__main__':
    current_directory = '.'

    files_to_clean = {
        5: 'timings_1.csv',
        10: 'timings_2.csv',
        20: 'timings_3.csv',
        30: 'timings_4.csv',
        40: 'timings_5.csv',
        50: 'timings_6.csv',
        100: 'timings_7.csv',
    }
    for tau, filename in files_to_clean.items():
        input_path = os.path.join(current_directory, filename)
        base_name, extension = os.path.splitext(filename)
        output_filename = f"{base_name}_cleaned{extension}"
        output_path = os.path.join(current_directory, output_filename)
        clean_iat_data(input_path, output_path, tau)

    print("All data cleaning tasks are complete.")