import pandas as pd
import numpy as np
import sys
import textwrap

def decode_timings(csv_file, threshold=150.0):
    df = pd.read_csv(csv_file)
    timings = df['Time'].values 

    bits = ['0' if t < threshold else '1' for t in timings]
    message = ""
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) < 8:
            break
        ascii_val = int(''.join(byte), 2)
        print(f"Byte {i//8}: bits={''.join(byte)}, ascii_val={ascii_val}") 
        if 32 <= ascii_val <= 126: 
            message += chr(ascii_val)
        else:
            message += '?'

    return bits, message


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python offline_decode.py timings.csv [threshold_ms]") 
        sys.exit(1)

    csv_file = sys.argv[1]
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0  

    bits, message = decode_timings(csv_file, threshold)
    with open("decoded_bits.txt", "w") as f:
        f.write("".join(bits))

    with open("decoded_message.txt", "w") as f:
        for line in textwrap.wrap(message, width=70):
            f.write(line + "\n")