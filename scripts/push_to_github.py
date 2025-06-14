#push_to_github.py

#!/usr/bin/env python3
import os
import base64
import json
import requests

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ["GITHUB_PAT_LOG_PUSH"]
REPO_OWNER   = "VanessaKingsleyHerts"
REPO_NAME    = "BidShopping"
BRANCH       = "main"
FILE_PATH    = "data/all_logs.csv"
COMMIT_MSG   = "ci: update merged CI log dataset [skip ci]"
# ────────────────────────────────────────────────────────────────────────────────

# Read and encode content
with open(FILE_PATH, "rb") as f:
    content = base64.b64encode(f.read()).decode()

# GitHub API URL
url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
# Choose header type based on token prefix
if GITHUB_TOKEN.startswith(("ghp_", "github_pat_")):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
else:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

# Debug prints
print(">>>> [push] API PUT URL:", url)
print(">>>> [push] Using headers:", {k: ("<hidden>" if k=="Authorization" else v) for k,v in headers.items()})

# Get the SHA of existing file if present
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

# Debug payload keys
print(">>>> [push] Payload keys:", list(payload.keys()))
print(">>>> [push] Payload size (bytes):", len(json.dumps(payload)))

# Perform the PUT
resp = requests.put(url, headers=headers, data=json.dumps(payload))

# Debug response
print(">>>> [push] Response code:", resp.status_code)
print(">>>> [push] Response text:", resp.text)

if resp.status_code in (200, 201):
    print(f"✅ [push] Successfully pushed {FILE_PATH} to GitHub.")
else:
    print(f"❌ [push] Failed to push to GitHub: {resp.status_code}")
    exit(1)
