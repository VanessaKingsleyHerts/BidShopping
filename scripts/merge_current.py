#ci: add merge_current.py for incremental log merge

#!/usr/bin/env python3
import os
import pandas as pd

# Paths
pipe_id = os.environ["CI_PIPELINE_ID"]
raw_path = f"data/raw/{pipe_id}.csv"
master_path = "data/all_logs.csv"

# Load today’s log
try:
    today = pd.read_csv(raw_path)
except FileNotFoundError:
    print(f"⚠️ No raw log found at {raw_path}")
    exit(1)

# Load or initialize master
if os.path.exists(master_path):
    master = pd.read_csv(master_path)
else:
    master = pd.DataFrame()

# Concatenate and dedupe
combined = pd.concat([master, today], ignore_index=True).drop_duplicates()
combined.to_csv(master_path, index=False)
print(f"✅ Merged {len(today)} rows; master now has {len(combined)} rows")
