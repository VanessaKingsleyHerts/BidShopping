#!/usr/bin/env python3
import os
import sys
import io
import zipfile
import requests

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GITLAB_API_URL = "https://gitlab.com/api/v4"
PROJECT_ID     = os.environ.get("CI_PROJECT_ID")
PRIVATE_TOKEN  = os.environ.get("GITLAB_PAT_DOWNLOAD_LOGS")
TARGET_DIR     = "data/raw"
# ────────────────────────────────────────────────────────────────────────────────

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
    resp = requests.get(
        f"{GITLAB_API_URL}/projects/{PROJECT_ID}/pipelines/{pid}/jobs",
        headers=HEADERS
    )
    resp.raise_for_status()
    return resp.json()

def download_artifacts_zip(job_id):
    """Download the full artifact zip for a job."""
    resp = requests.get(
        f"{GITLAB_API_URL}/projects/{PROJECT_ID}/jobs/{job_id}/artifacts",
        headers=HEADERS,
        stream=True
    )
    if resp.status_code == 200:
        return io.BytesIO(resp.content)
    return None

def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    page = 1
    downloaded, skipped = 0, []

    while True:
        pipelines = fetch_pipelines(page)
        if not pipelines:
            break

        for p in pipelines:
            pid = p["id"]
            jobs = fetch_jobs(pid)
            for j in jobs:
                if j.get("artifacts_file"):
                    buf = download_artifacts_zip(j["id"])
                    if not buf:
                        print(f"[!] Could not fetch artifacts ZIP for job {j['id']}")
                        continue

                    with zipfile.ZipFile(buf) as z:
                        namelist = z.namelist()
                        print(f"[DEBUG] Artifact contents for job {j['id']}: {namelist}")

                        # Try known candidate paths
                        candidates = [
                            "logs/ci_logs.csv",
                            "bidshopping/logs/ci_logs.csv",
                            f"{PROJECT_ID}/logs/ci_logs.csv",
                        ]
                        for candidate in candidates:
                            if candidate in namelist:
                                data = z.read(candidate)
                                break
                        else:
                            print(f"[!] ci_logs.csv not found in ZIP; skipping pipeline {pid}")
                            continue

                    out_path = os.path.join(TARGET_DIR, f"{pid}.csv")
                    with open(out_path, "wb") as f:
                        f.write(data)
                    print(f"✅ Saved: {out_path}")
                    downloaded += 1
                    break
            else:
                skipped.append(pid)

        page += 1

    print(f"\n🎉 Done—downloaded {downloaded} log files into {TARGET_DIR}")
    if skipped:
        print(f"[!] Skipped {len(skipped)} pipelines with no artifacts: {skipped}")

if __name__ == "__main__":
    main()
