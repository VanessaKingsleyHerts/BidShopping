# scripts/merge_ci_logs.py

import pandas as pd
import glob

files = glob.glob("data/raw/*.csv")
dfs = []
skipped = []

for f in files:
    try:
        # Use the Python engine and skip any bad lines
        df = pd.read_csv(
            f,
            engine="python",
            on_bad_lines="skip",  # skips rows that don't parse
        )

        # Ensure we always have a 'label' column
        if "label" not in df.columns:
            df["label"] = df["exit_code"].apply(
                lambda x: "success" if x == 0 else "failure"
            )

        dfs.append(df)
    except Exception as e:
        skipped.append((f, str(e)))

# Report skips
if skipped:
    print(f"[!] Skipped {len(skipped)} files due to parsing errors:")
    for fn, err in skipped:
        print(f"   - {fn}: {err}")

# Merge and write
if dfs:
    merged = pd.concat(dfs, ignore_index=True)
    merged.to_csv("data/all_logs.csv", index=False)
    print(f"✅ Merged {len(merged)} rows from {len(dfs)} files into data/all_logs.csv")
else:
    print("❌ No valid CSVs to merge.")
