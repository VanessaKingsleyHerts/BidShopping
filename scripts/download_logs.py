import os, requests

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GITLAB_API_URL = "https://gitlab.com/api/v4"
PROJECT_ID      = os.environ.get("PROJECT_ID")
PRIVATE_TOKEN   = os.environ.get("GITLAB_PAT_DOWNLOAD_LOGS")
if not PRIVATE_TOKEN:
    raise RuntimeError("Please set the GITLAB_PAT_DOWNLOAD_LOGS environment variable before running.")
TARGET_DIR      = "data/raw"
# ────────────────────────────────────────────────────────────────────────────────

def fetch_pipelines(page=1):
    url = f"{GITLAB_API_URL}/projects/{PROJECT_ID}/pipelines"
    params = {"per_page": 100, "page": page}
    headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
    resp = requests.get(url, params=params, headers=headers)
    return resp.json()

def fetch_jobs(pipeline_id):
    url = f"{GITLAB_API_URL}/projects/{PROJECT_ID}/pipelines/{pipeline_id}/jobs"
    headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
    return requests.get(url, headers=headers).json()

def download_artifact(job_id, out_path):
    url = f"{GITLAB_API_URL}/projects/{PROJECT_ID}/jobs/{job_id}/artifacts/logs/ci_logs.csv"
    headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
    r = requests.get(url, headers=headers, stream=True)
    if r.status_code == 200:
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        print(f"Saved: {out_path}")
    else:
        print(f"[!] No artifact for job {job_id}: {r.status_code}")

def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    page = 1
    downloaded = 0

    while True:
        pipes = fetch_pipelines(page=page)
        if not pipes:
            break
        for p in pipes:
            jobs = fetch_jobs(p["id"])
            # find the “test” stage job (which has our logs)
            for j in jobs:
                if j["stage"] == "test" and j["status"] in ("success","failed"):
                    out_file = os.path.join(TARGET_DIR, f"{p['id']}.csv")
                    if not os.path.exists(out_file):
                        download_artifact(j["id"], out_file)
                        downloaded += 1
                    break
        page += 1

    print(f"\nDone—downloaded {downloaded} log files.")

if __name__ == "__main__":
    main()
