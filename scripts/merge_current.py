#!/usr/bin/env python3
import os
import pandas as pd
import hashlib

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
    print(f"⚠️ [merge] No raw log found at {raw_path}")
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

# 3) Merge and de-duplicate
combined = pd.concat([master, today], ignore_index=True).drop_duplicates()

# 4) Compare file hashes
def sha256sum(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

if os.path.exists(master_path):
    before_hash = sha256sum(master_path)
else:
    before_hash = "<none>"

combined.to_csv(master_path, index=False)

after_hash = sha256sum(master_path)

print(f"[DEBUG][merge] File hash before: {before_hash}")
print(f"[DEBUG][merge] File hash after:  {after_hash}")

added = len(combined) - len(master)
print(f"[DEBUG][merge] Rows added this run: {added}")
print(f"[DEBUG][merge] Final total rows: {len(combined)}")

if before_hash == after_hash:
    print("⚠️ [merge] No actual content change in all_logs.csv")
else:
    print("✅ [merge] all_logs.csv content changed — new rows added.")
