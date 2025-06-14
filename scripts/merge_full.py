#merge_full.py

#!/usr/bin/env python3
import os
import csv
import pandas as pd
from glob import glob

RAW_DIR = "data/raw"
OUT_CSV = "data/all_logs.csv"

# 1) Load existing master
if os.path.exists(OUT_CSV):
    master = pd.read_csv(OUT_CSV)
    print(f"[INFO] Loaded master with {len(master)} rows")
else:
    master = pd.DataFrame()
    print("[INFO] No master file found, starting fresh")

# 2) Read & normalize each raw CSV
new_records = []
for path in sorted(glob(f"{RAW_DIR}/*.csv")):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print(f"[WARN] {path} is empty—skipping")
            continue

        ncols = len(header)
        rows = []
        for row in reader:
            if len(row) > ncols:
                # merge extras into last column
                row = row[:ncols-1] + [','.join(row[ncols-1:])]
            elif len(row) < ncols:
                # pad missing
                row = row + [''] * (ncols - len(row))
            rows.append(row)

        print(f"[INFO] Read {len(rows)} rows from {os.path.basename(path)} (expected cols={ncols})")
        if not rows:
            continue

        df = pd.DataFrame(rows, columns=header)
        df["pipeline_id"] = int(os.path.splitext(os.path.basename(path))[0])
        new_records.append(df)

if not new_records:
    print("⚠️ No new rows found in raw logs—nothing to merge.")
    exit(0)

# 3) Concatenate all new records
new_all = pd.concat(new_records, ignore_index=True)
print(f"[INFO] Total new rows to append: {len(new_all)}")

# 4) Append to master
combined = pd.concat([master, new_all], ignore_index=True)
print(f"[INFO] Rows before dedup: {len(combined)}")

# 5) Optionally drop duplicates on key columns
combined = combined.drop_duplicates(
    subset=["pipeline_id", "timestamp", "command", "tag"],
    keep="first"
)
print(f"[INFO] Rows after dedup: {len(combined)}")

# 6) Save
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
combined.to_csv(OUT_CSV, index=False)
print(f"✅ Written {len(combined)} total rows to {OUT_CSV}")
