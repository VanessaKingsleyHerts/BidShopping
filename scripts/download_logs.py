#!/usr/bin/env python3
import os
import sys
import time
import requests

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GITLAB_API_URL = "https://gitlab.com/api/v4"
PROJECT_ID     = os.environ.get("PROJECT_ID")
PRIVATE_TOKEN  = os.environ.get("GITLAB_PAT_DOWNLOAD_LOGS")
TARGET_DIR     = "data/raw"
# ────────────────────────────────────────────────────────────────────────────────

if not PROJECT_ID:
    print("❌ ERROR: PROJECT_ID environment variable is not set.")
    sys.exit(1)

if not PRIVATE_TOKEN:
    print("❌ ERROR: GITLAB_PAT_DOWNLOAD_LOGS environment variable is not set.")
    sys.exit(1)

HEADERS = {"PRIVATE-TOKEN": PRIVATE_TOKEN}

def fetch_pipelines(page=1):
    url = f"{GITLAB_API_URL}/projects/{PROJECT_ID}/pipelines"
    params = {"per_page": 100, "page": page}
    resp = requests.get(url, params=params, headers=HEADERS)
    if resp.status_code != 200:
        print(f"❌ Failed to fetch pipelines (status {resp.status_code}):")
        print(resp.text)
        sys.exit(1)
    data = resp.json()
    if not isinstance(data, list):
        print("❌ Unexpected response format for pipelines:")
        print(data)
        sys.exit(1)
    return data

def fetch_jobs(pipeline_id):
    url = f"{GITLAB_API_URL}/projects/{PROJECT_ID}/pipelines/{pipeline_id}/jobs"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print(f"❌ Failed to fetch jobs for pipeline {pipeline_id} (status {resp.status_code}):")
        print(resp.text)
        sys.exit(1)
    data = resp.json()
    if not isinstance(data, list):
        print(f"❌ Unexpected response format for jobs of pipeline {pipeline_id}:")
        print(data)
        sys.exit(1)
    return data

def download_artifact(job_id, out_path):
    url = f"{GITLAB_API_URL}/projects/{PROJECT_ID}/jobs/{job_id}/artifacts/logs/ci_logs.csv"
    resp = requests.get(url, headers=HEADERS, stream=True)
    if resp.status_code == 200:
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)
        print(f"✅ Saved: {out_path}")
    else:
        print(f"[!] No artifact for job {job_id}: HTTP {resp.status_code}")

def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    page = 1
    downloaded = 0

    while True:
        pipelines = fetch_pipelines(page=page)
        if not pipelines:
            break

        for p in pipelines:
            pid = p.get("id")
            if not pid:
                continue

            jobs = fetch_jobs(pid)
            # find the “test” stage job (which has our logs)
            for j in jobs:
                if j.get("stage") == "test" and j.get("status") in ("success", "failed"):
                    out_file = os.path.join(TARGET_DIR, f"{pid}.csv")
                    if not os.path.exists(out_file):
                        download_artifact(j["id"], out_file)
                        downloaded += 1
                    break

        page += 1

    print(f"\n🎉 Done—downloaded {downloaded} log files into {TARGET_DIR}.")

if __name__ == "__main__":
    main()
