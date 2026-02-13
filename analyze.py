"""
Analyze IPD patterns in mss_ipd.csv to understand detection vulnerability
"""
from collections import Counter

def analyze_ipd(filepath='data/fuzzy_o.csv'):
    # Load the combined file
    with open(filepath, 'r') as f:
        lines = f.readlines()[1:]  # skip header
    ipds = [float(l.strip()) for l in lines if l.strip()]

    print(f"=" * 60)
    print(f"IPD PATTERN ANALYSIS")
    print(f"=" * 60)
    print(f"\nTotal IPD values: {len(ipds):,}")
    
    # Basic stats
    print(f"\n{'='*60}")
    print(f"BASIC STATISTICS")
    print(f"{'='*60}")
    print(f"  Min:  {min(ipds):.6f}")
    print(f"  Max:  {max(ipds):.6f}")
    print(f"  Mean: {sum(ipds)/len(ipds):.6f}")
    
    # Variance
    mean = sum(ipds)/len(ipds)
    variance = sum((x - mean)**2 for x in ipds) / len(ipds)
    std = variance ** 0.5
    print(f"  Std:  {std:.6f}")

    # Value distribution - round to 2 decimals
    print(f"\n{'='*60}")
    print(f"VALUE DISTRIBUTION (rounded to 2 decimals)")
    print(f"{'='*60}")
    rounded = [round(x, 2) for x in ipds]
    counts = Counter(rounded)
    print(f"\nTop 20 most common values:")
    for val, cnt in counts.most_common(20):
        bar = '█' * int(cnt/len(ipds)*100)
        print(f"  {val:.2f}: {cnt:>6} ({cnt/len(ipds)*100:>5.2f}%) {bar}")

    # Bimodal clustering analysis
    print(f"\n{'='*60}")
    print(f"BIMODAL CLUSTERING ANALYSIS")
    print(f"{'='*60}")
    
    thresholds = [0.11, 0.12, 0.125, 0.13]
    for thresh in thresholds:
        low = [x for x in ipds if x < thresh]
        high = [x for x in ipds if x >= thresh]
        print(f"\n  Threshold: {thresh}")
        print(f"    < {thresh}: {len(low):>6} ({len(low)/len(ipds)*100:>5.1f}%) - likely bit 0")
        print(f"    >= {thresh}: {len(high):>6} ({len(high)/len(ipds)*100:>5.1f}%) - likely bit 1")

    # Histogram
    print(f"\n{'='*60}")
    print(f"HISTOGRAM (Manual bins)")
    print(f"{'='*60}")
    bins = [
        (0.095, 0.100), (0.100, 0.105), (0.105, 0.110), (0.110, 0.115),
        (0.115, 0.120), (0.120, 0.130), (0.130, 0.140), (0.140, 0.150),
        (0.150, 0.155), (0.155, 0.160), (0.160, 0.165), (0.165, 0.170)
    ]
    print(f"\n  Range          Count      %     Visual")
    print(f"  {'-'*50}")
    for lo, hi in bins:
        cnt = len([x for x in ipds if lo <= x < hi])
        bar = '█' * int(cnt/len(ipds)*150)
        print(f"  {lo:.3f}-{hi:.3f}: {cnt:>6} ({cnt/len(ipds)*100:>5.2f}%) {bar}")

    # Pattern detection - check if sorted values show clear separation
    print(f"\n{'='*60}")
    print(f"SORTED VALUE ANALYSIS")
    print(f"{'='*60}")
    sorted_ipds = sorted(ipds)
    n = len(sorted_ipds)
    percentiles = [0, 10, 25, 40, 50, 60, 75, 90, 100]
    print(f"\n  Percentile distribution:")
    for p in percentiles:
        idx = min(int(n * p / 100), n-1)
        print(f"    {p:>3}th percentile: {sorted_ipds[idx]:.6f}")

    # Gap analysis - find the biggest gap in sorted values
    print(f"\n  Looking for bimodal gap...")
    gaps = []
    for i in range(1, len(sorted_ipds)):
        gap = sorted_ipds[i] - sorted_ipds[i-1]
        gaps.append((gap, sorted_ipds[i-1], sorted_ipds[i], i))
    
    top_gaps = sorted(gaps, reverse=True)[:5]
    print(f"\n  Top 5 largest gaps (indicates clustering):")
    for gap, low_val, high_val, idx in top_gaps:
        pct = idx / n * 100
        print(f"    Gap: {gap:.6f} between {low_val:.6f} and {high_val:.6f} (at {pct:.1f}% of data)")

    # Cross-message pattern analysis
    print(f"\n{'='*60}")
    print(f"CROSS-MESSAGE PATTERN ANALYSIS")
    print(f"{'='*60}")
    
    # Assuming each message has ~2041 IPDs (based on 204100 / 100 messages)
    msg_size = len(ipds) // 100
    print(f"\n  Estimated IPDs per message: ~{msg_size}")
    
    # Check if same positions across messages have similar values
    print(f"\n  Checking position correlation across messages...")
    sample_positions = [0, 10, 100, 500, 1000]
    for pos in sample_positions:
        if pos < msg_size:
            values_at_pos = [ipds[i * msg_size + pos] for i in range(min(10, 100)) if i * msg_size + pos < len(ipds)]
            if values_at_pos:
                avg = sum(values_at_pos) / len(values_at_pos)
                var = sum((x - avg)**2 for x in values_at_pos) / len(values_at_pos)
                print(f"    Position {pos}: avg={avg:.4f}, std={var**0.5:.6f}, values={[f'{v:.3f}' for v in values_at_pos[:5]]}")

    print(f"\n{'='*60}")
    print(f"DETECTION VULNERABILITY ASSESSMENT")
    print(f"{'='*60}")
    
    # Count distinct rounded values
    unique_rounded = len(counts)
    print(f"\n  Unique values (2 decimal): {unique_rounded}")
    
    # Calculate entropy-like measure
    total = len(ipds)
    entropy = 0
    for cnt in counts.values():
        p = cnt / total
        if p > 0:
            import math
            entropy -= p * math.log2(p)
    print(f"  Distribution entropy: {entropy:.4f} bits")
    print(f"  (Lower entropy = more predictable = easier to detect)")
    
    # Concentration ratio
    top3 = sum(cnt for _, cnt in counts.most_common(3))
    print(f"  Top 3 values concentration: {top3/total*100:.1f}%")
    print(f"  (Higher concentration = more obvious pattern)")

if __name__ == "__main__":
    analyze_ipd()
