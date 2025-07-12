#!/usr/bin/env python3
import os
import base64
import json
import requests
import pandas as pd
from datetime import datetime

try:
    from ci.log_schema import EXPECTED_COLS
except ModuleNotFoundError:
    import sys
    sys.path.append('.')
    from ci.log_schema import EXPECTED_COLS

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ["GITHUB_PAT_LOG_PUSH"]
REPO_OWNER   = "VanessaKingsleyHerts"
REPO_NAME    = "BidShopping"
BRANCH       = "main"
FILE_PATH    = "data/all_logs.csv"
now          = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
COMMIT_MSG   = f"ci: update merged CI log dataset ({now} UTC) [skip ci]"
# ────────────────────────────────────────────────────────────────────────────────

if not GITHUB_TOKEN:
    print("❌ ERROR: GITHUB_PAT_LOG_PUSH not set")
    exit(1)

if not os.path.exists(FILE_PATH):
    print(f"❌ ERROR: {FILE_PATH} does not exist — nothing to push.")
    exit(1)

try:
    df = pd.read_csv(FILE_PATH)
    if list(df.columns) != EXPECTED_COLS:
        print(f"❌ Column mismatch in {FILE_PATH}")
        exit(1)
except Exception as e:
    print(f"❌ Error validating {FILE_PATH}: {e}")
    exit(1)

# Read and encode content
with open(FILE_PATH, "rb") as f:
    content = base64.b64encode(f.read()).decode()

url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

# Token prefix-aware auth header
if GITHUB_TOKEN.startswith(("ghp_", "github_pat_")):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
else:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

# Get SHA of existing file if it exists
r_get = requests.get(url, headers=headers, params={"ref": BRANCH})
if r_get.status_code == 200:
    sha = r_get.json().get("sha")
    print(">>>> [push] Existing file SHA:", sha)
else:
    print(">>>> [push] No existing file found (status", r_get.status_code, ")")
    sha = None

# Build payload
payload = {
    "message": COMMIT_MSG,
    "content": content,
    "branch": BRANCH,
}
if sha:
    payload["sha"] = sha

# Push
resp = requests.put(url, headers=headers, data=json.dumps(payload))

# Response handling
print(">>>> [push] Response code:", resp.status_code)
if resp.status_code in (200, 201):
    print(f"✅ [push] Successfully pushed {FILE_PATH} to GitHub.")
else:
    print(f"❌ [push] Failed to push to GitHub: {resp.status_code}")
    print(resp.text)
    exit(1)
