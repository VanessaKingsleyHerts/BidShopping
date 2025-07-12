#!/usr/bin/env python3
import os
import pandas as pd
import hashlib
import sys
try:
    from ci.log_schema import EXPECTED_COLS
except ModuleNotFoundError:
    import sys
    sys.path.append('.')
    from ci.log_schema import EXPECTED_COLS

pipe_id     = os.environ["CI_PIPELINE_ID"]
raw_path    = f"data/raw/{pipe_id}.csv"
master_path = "data/all_logs.csv"

# 1) Read current log
print(f"[DEBUG][merge] Reading current log: {raw_path}")
try:
    current = pd.read_csv(raw_path, encoding="utf-8")
except UnicodeDecodeError:
    current = pd.read_csv(raw_path, encoding="utf-8-sig")
except FileNotFoundError:
    print(f"⚠️ [merge] No raw log found at {raw_path}")
    sys.exit(1)

print(f"[DEBUG][merge] Current has {len(current)} rows, columns: {list(current.columns)}")

try:
    current = current[EXPECTED_COLS]
except KeyError as e:
    print(f"❌ [merge] Column mismatch: {e}")
    sys.exit(1)

# 2) Read or initialize master
if os.path.exists(master_path):
    print(f"[DEBUG][merge] Reading existing master: {master_path}")
    master = pd.read_csv(master_path)
    print(f"[DEBUG][merge] Master before merge has {len(master)} rows")
else:
    print("[DEBUG][merge] No existing master found, starting fresh")
    master = pd.DataFrame(columns=EXPECTED_COLS)

# 3) Merge and de-duplicate
combined = pd.concat([master, current], ignore_index=True).drop_duplicates()

# 4) Hash compare
def sha256sum(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

before_hash = sha256sum(master_path) if os.path.exists(master_path) else "<none>"
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

print("🔍 [merge] Sample of final saved file:")
print(combined.tail(5).to_string(index=False))
print("🔍 [merge] First few rows of current raw log:")
print(current.head(5).to_string(index=False))
