import matplotlib.pyplot as plt
import pandas as pd
import re

# Read the combined analysis file
with open('combined_analysis.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Function to parse a table section
def parse_table(body):
    lines = body.split('\n')
    data_lines = [line for line in lines if re.match(r'\s*\d+\.\d+', line)]
    if not data_lines:
        return None
    df = pd.DataFrame([line.split() for line in data_lines], columns=['Threshold', 'FPR', 'FNR', 'Total_Error'])
    df = df.astype(float)
    return df

# Parse ε-similarity sections (Covert and Fuzzed vs Legit)
eps_similarity_data = {}
sections = re.split(r'(--- .*? ---)', content)[1:]
for i in range(0, len(sections), 2):
    header = sections[i].strip()
    body = sections[i+1].strip()
    if 'E-similarity FP vs. FN Balance Analysis' in header and 'Enhanced' not in header:
        type_match = re.search(r'(Covert|Fuzzed)', header)
        if type_match:
            data_type = type_match.group(1)
            eps_matches = re.findall(r'ε = ([\d.]+)', body)
            for eps in eps_matches:
                table_start = body.find(f'--- Results for ε = {eps} ---')
                if table_start != -1:
                    table_body = body[table_start:]
                    table_end = table_body.find('---')
                    if table_end != -1:
                        table_body = table_body[:table_end]
                    df = parse_table(table_body)
                    if df is not None:
                        key = f'{data_type}_{eps}'
                        eps_similarity_data[key] = df

# Plot ε-similarity (Covert and Fuzzed vs Legit)
plt.figure(figsize=(12, 8))
colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
eps_values = ['0.005', '0.008', '0.01', '0.02', '0.03', '0.1']
for idx, eps in enumerate(eps_values):
    for data_type in ['Covert', 'Fuzzed']:
        key = f'{data_type}_{eps}'
        if key in eps_similarity_data:
            df = eps_similarity_data[key]
            linestyle = '--' if data_type == 'Fuzzed' else '-'
            label = f'{data_type} (ε={eps})'
            plt.plot(df['Threshold'], df['Total_Error'], label=label, linestyle=linestyle, color=colors[idx])
plt.xlabel('Threshold')
plt.ylabel('Total_Error')
plt.title('ε-Similarity: Total Error vs Threshold (Covert and Fuzzed vs Legit)')
plt.legend()
plt.grid(True)
plt.savefig('eps_similarity_covert_fuzzed.png', dpi=300, bbox_inches='tight')
plt.close()

# Parse remedy (Enhanced ε-similarity) sections
remedy_data = {}
for i in range(0, len(sections), 2):
    header = sections[i].strip()
    body = sections[i+1].strip()
    if 'Enhanced ε-similarity' in header:
        eps_matches = re.findall(r'ε = ([\d.]+)', body)
        for eps in eps_matches:
            table_start = body.find(f'--- Results for ε = {eps} ---')
            if table_start != -1:
                table_body = body[table_start:]
                table_end = table_body.find('---')
                if table_end != -1:
                    table_body = table_body[:table_end]
                df = parse_table(table_body)
                if df is not None:
                    remedy_data[eps] = df

# Plot remedy analysis
plt.figure(figsize=(12, 8))
for idx, eps in enumerate(eps_values):
    if eps in remedy_data:
        df = remedy_data[eps]
        label = f'ε={eps}'
        plt.plot(df['Threshold'], df['Total_Error'], label=label, color=colors[idx])
plt.xlabel('Threshold')
plt.ylabel('Total_Error')
plt.title('Remedy Analysis (Enhanced ε-Similarity): Total Error vs Threshold')
plt.legend()
plt.grid(True)
plt.savefig('remedy_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("Saved eps_similarity_covert_fuzzed.png and remedy_analysis.png")