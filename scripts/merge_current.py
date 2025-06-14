#!/usr/bin/env python3
import os
import pandas as pd

# ─── CONFIG ───────────────────────────────────────────────────────────────────
pipe_id     = os.environ["CI_PIPELINE_ID"]
raw_path    = f"data/raw/{pipe_id}.csv"
master_path = "data/all_logs.csv"
# ────────────────────────────────────────────────────────────────────────────────

# 1) Read today's log
print(f"[DEBUG][merge] Reading today's log: {raw_path}")
try:
    today = pd.read_csv(raw_path)
except FileNotFoundError:
    print("⚠️ [merge] No raw log found at", raw_path)
    exit(1)
print(f"[DEBUG][merge] Today has {len(today)} rows, columns: {list(today.columns)}")

# 2) Read or initialize master
if os.path.exists(master_path):
    print(f"[DEBUG][merge] Reading existing master: {master_path}")
    master = pd.read_csv(master_path)
    print(f"[DEBUG][merge] Master before merge has {len(master)} rows")
else:
    print("[DEBUG][merge] No existing master found, starting fresh")
    master = pd.DataFrame()

# 3) Concatenate and de-duplicate
combined = pd.concat([master, today], ignore_index=True).drop_duplicates()
combined.to_csv(master_path, index=False)
added = len(combined) - len(master)
print(f"[DEBUG][merge] After merge master has {len(combined)} rows")
print(f"✅ [merge] Merged pipeline {pipe_id}: added {added} new rows")
