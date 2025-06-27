#predict_and_heal.py

#!/usr/bin/env python3
import os, sys, csv, joblib, subprocess, argparse, shlex
import numpy as np
import pandas as pd
from keras.models import load_model

# Paths to models
RF_MODEL   = os.path.join(os.path.dirname(__file__), "../notebooks/models/rf_model.joblib")
RF_SCALER  = os.path.join(os.path.dirname(__file__), "../notebooks/models/rf_scaler.joblib")
LSTM_MODEL = os.path.join(os.path.dirname(__file__), "../notebooks/models/lstm_model.h5")

# Constants
SEQ_LEN  = 2    # build + lint
FEATURES = ["log_duration","cpu_pct_avg","mem_mb","tag_code"]

# Determine healing mode (baseline or ml)
MODE = os.environ.get("HEAL_MODE", "ml")  # default to ml

# Ensure logs header includes mode column
LOG_HEADER: list[str] = []

def ensure_header(csv_path="logs/ci_logs.csv"):
    global LOG_HEADER
    if not os.path.exists(csv_path):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            LOG_HEADER = [
                "timestamp","command","duration_s","exit_code",
                "cpu_pct_avg","mem_kb_max","tag","status",
                "pipeline_id","mode"
            ]
            writer.writerow(LOG_HEADER)
    else:
        with open(csv_path) as f:
            reader = csv.reader(f)
            LOG_HEADER = next(reader)


def load_latest_log():
    with open("logs/ci_logs.csv") as f:
        rows = list(csv.DictReader(f))
    return rows[-1]


def extract_rf_features(row):
    df_row = pd.DataFrame([row])
    # Map tag to encoded code matching training
    tag_map = {"build": 0, "lint": 1, "test": 2}
    # Create feature DataFrame with correct columns
    feat = pd.DataFrame({
        "log_duration": np.log1p(df_row["duration_s"].astype(float)),
        "cpu_pct_avg": df_row["cpu_pct_avg"].astype(float),
        "mem_mb": df_row["mem_kb_max"].astype(float) / 1024,
        "hour": pd.to_datetime(df_row["timestamp"]).dt.hour,
        "dayofweek": pd.to_datetime(df_row["timestamp"]).dt.dayofweek,
        "tag_code": df_row["tag"].map(tag_map).astype(int)
    })
    # Load scaler and enforce feature order
    scaler = joblib.load(RF_SCALER)
    feat = feat[scaler.feature_names_in_]
    # Transform and return
    return scaler.transform(feat)


def predict_rf():
    row = load_latest_log()
    X = extract_rf_features(row)
    rf = joblib.load(RF_MODEL)
    return rf.predict(X)[0]  # 1=pass, 0=fail


def predict_lstm(pipeline_id):
    # Read raw logs and filter for this pipeline
    df_logs = pd.read_csv("logs/ci_logs.csv")
    seq = df_logs[df_logs["pipeline_id"] == str(pipeline_id)].sort_values("timestamp")
    if seq.empty:
        return 1  # no data, assume pass
    # Recompute features for each row
    tag_map = {"build":0, "lint":1, "test":2}
    feat_df = pd.DataFrame({
        "log_duration": np.log1p(seq["duration_s"].astype(float)),
        "cpu_pct_avg": seq["cpu_pct_avg"].astype(float),
        "mem_mb": seq["mem_kb_max"].astype(float)/1024,
        "tag_code": seq["tag"].map(tag_map).astype(int)
    })
    # Use only the first SEQ_LEN entries (pad if needed)
    arr = feat_df.values
    if arr.shape[0] < SEQ_LEN:
        pad = np.zeros((SEQ_LEN - arr.shape[0], arr.shape[1]))
        arr = np.vstack([arr, pad])
    else:
        arr = arr[:SEQ_LEN]
    # Reshape into (1, seq_len, n_features)
    arr = arr.reshape((1, SEQ_LEN, arr.shape[1]))
    lstm = load_model(LSTM_MODEL)
    prob = lstm.predict(arr, verbose=0)[0,0]
    return int(prob > 0.5)  # 1=pass, 0=fail


def run_logged(command, tag, label=None, override_status=None):
    # Run the actual command to get the true exit code
    raw_code = subprocess.call(command, shell=True)

    # If override_status is given, use that instead
    status_flag = "--force-status " + override_status if override_status else ""

    # Build logging command
    log_cmd = f'python ci/ci_logger.py "{command}" --tag {tag} {status_flag}'
    if label:
        log_cmd += f' --label {label}'

    # Log the result (separate from actual command execution)
    subprocess.call(log_cmd, shell=True)
    return raw_code



def run_and_heal(command, tag, label=None):
    ensure_header()
    
    # 1) Initial run & log
    init_code = run_logged(command, tag, label)

    # 🧪 Optional Failure Injection for A/B testing
    if os.environ.get("INJECT_FAIL", "true").lower() == "true" and tag == "lint":
        print("[Injected Failure] Forcing lint stage to fail for experiment")
        init_code = 1
    
    # 2) If it failed, do exactly one retry and log it
    if init_code != 0:
        if MODE == "baseline":
            print(f"[Baseline] {tag} failed—retrying once")
            retry_code = run_logged(command, tag, label)
            return retry_code

        else:  # ML mode
            # RF-driven retry (only for lint/test)
            if tag in ("lint", "test") and predict_rf() == 0:
                print(f"[RF] {tag} anomaly—retrying once")
                retry_code = run_logged(command, tag, label)
                return retry_code

            # LSTM abort before test
            if tag == "lint" and predict_lstm(os.getenv("CI_PIPELINE_ID","0")) == 0:
                print("[LSTM] Pipeline predicted to fail—aborting before test")
                sys.exit(0)
                
    # If initial succeeded (or no retry triggered), return that code
    return init_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="Shell command to execute")
    parser.add_argument("--tag", required=True, help="Stage tag (build, lint, test)")
    parser.add_argument("--label", required=False, help="Optional short label for job")
    args = parser.parse_args()
    rc = run_and_heal(args.command, args.tag, args.label)
    sys.exit(rc)
