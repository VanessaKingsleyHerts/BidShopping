#!/usr/bin/env python3
import os, base64, json, requests, sys

# Config
GITHUB_TOKEN = os.environ["GITHUB_PAT_LOG_PUSH"]
REPO_OWNER   = "VanessaKingsleyHerts"
REPO_NAME    = "BidShopping"
BRANCH       = "main"
FILE_PATH    = "data/all_logs.csv"
COMMIT_MSG   = "ci: update merged CI log dataset [skip ci]"

# Read file and encode
with open(FILE_PATH, "rb") as f:
    content = base64.b64encode(f.read()).decode()

# Get the SHA of the existing file (if any)
url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
r = requests.get(url, headers=headers, params={"ref": BRANCH})
if r.status_code == 200:
    sha = r.json()["sha"]
else:
    sha = None

# Prepare payload
payload = {
    "message": COMMIT_MSG,
    "content": content,
    "branch": BRANCH,
}
if sha:
    payload["sha"] = sha

# PUT to create/update
resp = requests.put(url, headers=headers, data=json.dumps(payload))
if resp.status_code in (200, 201):
    print(f"✅ Successfully pushed {FILE_PATH} to GitHub.")
else:
    print("❌ Failed to push to GitHub:", resp.status_code, resp.text)
    sys.exit(1)
