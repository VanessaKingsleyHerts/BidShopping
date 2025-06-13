#!/usr/bin/env python3
import os, sys, io, zipfile, requests

GITLAB_API_URL = "https://gitlab.com/api/v4"
PROJECT_ID     = os.environ["CI_PROJECT_ID"]
PRIVATE_TOKEN  = os.environ.get("GITLAB_PAT_DOWNLOAD_LOGS")
TARGET_DIR     = "data/raw"

if not PRIVATE_TOKEN:
    print("❌ ERROR: GITLAB_PAT_DOWNLOAD_LOGS not set")
    sys.exit(1)

HEADERS = {"PRIVATE-TOKEN": PRIVATE_TOKEN}

def fetch_pipelines(page=1):
    r = requests.get(
        f"{GITLAB_API_URL}/projects/{PROJECT_ID}/pipelines",
        params={"per_page": 100, "page": page},
        headers=HEADERS
    )
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []

def fetch_jobs(pid):
    r = requests.get(f"{GITLAB_API_URL}/projects/{PROJECT_ID}/pipelines/{pid}/jobs", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def download_artifacts_zip(job_id):
    r = requests.get(
        f"{GITLAB_API_URL}/projects/{PROJECT_ID}/jobs/{job_id}/artifacts",
        headers=HEADERS, stream=True
    )
    if r.status_code == 200:
        return io.BytesIO(r.content)
    return None

def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    page = 1
    downloaded, skipped = 0, []

    while True:
        pipelines = fetch_pipelines(page)
        if page == 1:
            print(f"[DEBUG] First page pipelines (IDs): {[p['id'] for p in pipelines[:10]]}")
        if not pipelines:
            break

        for p in pipelines:
            pid = p["id"]
            print(f"\n[DEBUG] Inspecting Pipeline {pid} (status={p['status']}, ref={p['ref']})")
            jobs = fetch_jobs(pid)
            print(f"[DEBUG]  Jobs found: {[j['name']+'('+str(j.get('artifacts_file') is not None)+')' for j in jobs]}")
            for j in jobs:
                if j.get("artifacts_file"):
                    buf = download_artifacts_zip(j["id"])
                    if not buf:
                        print(f"[!] Could not fetch ZIP for job {j['id']}")
                        continue

                    with zipfile.ZipFile(buf) as z:
                        namelist = z.namelist()
                        print(f"[DEBUG]  ZIP contents: {namelist}")

                        if "logs/ci_logs.csv" in namelist:
                            data = z.read("logs/ci_logs.csv")
                        else:
                            print(f"[!]  No logs/ci_logs.csv in this ZIP")
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

    print(f"\n🎉 Done—downloaded {downloaded} log files.")
    if skipped:
        print(f"[!] Pipelines with no artifacts: {skipped[:10]}… (total {len(skipped)})")

if __name__ == "__main__":
    main()
