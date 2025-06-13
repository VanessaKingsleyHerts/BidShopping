# scripts/merge_ci_logs.py

import pandas as pd
import glob

# Define the exact columns we expect (including label)
COLUMNS = [
    "timestamp",
    "command",
    "duration_s",
    "exit_code",
    "cpu_pct_avg",
    "mem_kb_max",
    "tag",
    "label",
]

files = glob.glob("data/raw/*.csv")
dfs = []
skipped = []

for f in files:
    try:
        # Read raw lines
        with open(f, "r") as fh:
            lines = fh.readlines()

        # Filter out any header lines (7 or 8 fields)
        data_lines = []
        for line in lines:
            parts = line.strip().split(",")
            if parts[:7] == COLUMNS[:7]:
                # This is a header row — skip
                continue
            data_lines.append(line)

        # Parse the filtered data
        df = pd.read_csv(
            pd.compat.StringIO("".join(data_lines)),
            names=COLUMNS,
            header=None,
        )

        # If the original file had no 'label' column, Pandas will have 'label' NaN
        df["label"] = df["label"].fillna(
            df["exit_code"].apply(lambda x: "success" if int(x) == 0 else "failure")
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
