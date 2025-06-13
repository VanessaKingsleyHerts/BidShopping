#!/usr/bin/env python3
import os, sys, requests

GITLAB_API_URL = "https://gitlab.com/api/v4"
PROJECT_ID     = os.environ["PROJECT_ID"]
PRIVATE_TOKEN  = os.environ.get("GITLAB_PAT_DOWNLOAD_LOGS")
TARGET_DIR     = "data/raw"

if not PRIVATE_TOKEN:
    print("❌ ERROR: GITLAB_PAT_DOWNLOAD_LOGS not set")
    sys.exit(1)

HEADERS = {"PRIVATE-TOKEN": PRIVATE_TOKEN}

def fetch_pipelines(page=1):
    resp = requests.get(
        f"{GITLAB_API_URL}/projects/{PROJECT_ID}/pipelines",
        params={"per_page": 100, "page": page},
        headers=HEADERS
    )
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else []

def fetch_jobs(pid):
    resp = requests.get(f"{GITLAB_API_URL}/projects/{PROJECT_ID}/pipelines/{pid}/jobs", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def download_logs_from_job(job_id, pid):
    """Attempt to download logs/ci_logs.csv from this job."""
    url = f"{GITLAB_API_URL}/projects/{PROJECT_ID}/jobs/{job_id}/artifacts/logs/ci_logs.csv"
    r = requests.get(url, headers=HEADERS, stream=True)
    if r.status_code == 200:
        path = os.path.join(TARGET_DIR, f"{pid}.csv")
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        print(f"✅ Saved: {path}")
        return True
    return False

def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    downloaded, skipped = 0, []

    page = 1
    while True:
        pipes = fetch_pipelines(page)
        if not pipes:
            break

        for p in pipes:
            pid = p["id"]
            jobs = fetch_jobs(pid)
            for j in jobs:
                # any job with artifacts -> try download
                if j.get("artifacts_file"):
                    if download_logs_from_job(j["id"], pid):
                        downloaded += 1
                    else:
                        print(f"[!] Job {j['id']} has artifacts but no logs for pipeline {pid}")
                    break
            else:
                skipped.append(pid)

        page += 1

    print(f"\n🎉 Done—downloaded {downloaded} log files into {TARGET_DIR}")
    if skipped:
        print(f"[!] Skipped {len(skipped)} pipelines with no artifacts: {skipped}")

if __name__ == "__main__":
    main()
