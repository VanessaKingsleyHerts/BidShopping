#!/usr/bin/env python3
import os
import sys
import io
import zipfile
import requests

try:
    from ci.log_schema import EXPECTED_COLS
except ModuleNotFoundError:
    import sys
    sys.path.append('.')
    from ci.log_schema import EXPECTED_COLS

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GITLAB_API_URL = "https://gitlab.com/api/v4"
PROJECT_ID     = os.environ.get("PROJECT_ID")
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
    return resp.json()

def fetch_jobs(pid):
    resp = requests.get(
        f"{GITLAB_API_URL}/projects/{PROJECT_ID}/pipelines/{pid}/jobs",
        headers=HEADERS
    )
    resp.raise_for_status()
    return resp.json()

def download_artifacts_zip(job_id):
    resp = requests.get(
        f"{GITLAB_API_URL}/projects/{PROJECT_ID}/jobs/{job_id}/artifacts",
        headers=HEADERS, stream=True
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
            print(f"\n[DEBUG] Inspecting Pipeline {pid} (status={p['status']}, ref={p['ref']})")
            jobs = fetch_jobs(pid)

            for j in jobs:
                if not j.get("artifacts_file"):
                    continue

                buf = download_artifacts_zip(j["id"])
                if not buf:
                    print(f"[!] Could not fetch ZIP for job {j['id']}")
                    continue

                with zipfile.ZipFile(buf) as z:
                    namelist = z.namelist()
                    print("[DEBUG] Artifact contents:", namelist)

                    if "logs/ci_logs.csv" not in namelist:
                        print("[!] ci_logs.csv not found in this ZIP")
                        continue

                    raw_bytes = z.read("logs/ci_logs.csv")
                    text = raw_bytes.decode("utf-8-sig")
                    header = text.splitlines()[0].split(",")

                    if header != EXPECTED_COLS:
                        print(f"❌ [download] Skipping {pid} — column mismatch")
                        skipped.append(pid)
                        continue

                    out_path = os.path.join(TARGET_DIR, f"{pid}.csv")
                    with open(out_path, "w", encoding="utf-8", newline="") as f:
                        f.write(text)

                    print("✅ Saved:", out_path)
                    downloaded += 1
                    break
            else:
                skipped.append(pid)

        page += 1

    print(f"\n🎉 Done — downloaded {downloaded} logs into {TARGET_DIR}")
    if skipped:
        print("[!] Skipped", len(skipped), "pipelines:", skipped[:10])

if __name__ == "__main__":
    main()
