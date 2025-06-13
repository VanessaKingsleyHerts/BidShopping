# scripts/merge_ci_logs.py

import pandas as pd
import glob

files = glob.glob("data/raw/*.csv")
dfs = []

for f in files:
    try:
        df = pd.read_csv(f)

        # Fix column mismatch if needed
        if 'label' not in df.columns:
            df['label'] = df['exit_code'].apply(lambda x: 'success' if x == 0 else 'failure')

        dfs.append(df)
    except Exception as e:
        print(f"[!] Skipping {f}: {e}")

# Merge everything
if dfs:
    merged = pd.concat(dfs, ignore_index=True)
    merged.to_csv("data/all_logs.csv", index=False)
    print(f"✅ Merged {len(merged)} rows into data/all_logs.csv")
else:
    print("❌ No valid CSVs to merge.")
