#!/usr/bin/env python3
import os, sys, csv, joblib, subprocess, argparse
import numpy as np
import pandas as pd
from keras.models import load_model

# Paths to models
RF_MODEL = os.path.join(os.path.dirname(__file__), "../notebooks/models/rf_model.joblib")
RF_SCALER = os.path.join(os.path.dirname(__file__), "../notebooks/models/rf_scaler.joblib")
LSTM_MODEL = os.path.join(os.path.dirname(__file__), "../notebooks/models/lstm_model.h5")

# Constants
SEQ_LEN = 2    # build + lint
FEATURES = ["log_duration","cpu_pct_avg","mem_mb","tag_code"]

def load_latest_log():
    with open("logs/ci_logs.csv") as f:
        rows = list(csv.DictReader(f))
    return rows[-1]

def extract_rf_features(row):
    # Build a single-row DataFrame
    df = pd.DataFrame([row])
    feat = pd.DataFrame({
        "log_duration": np.log1p(df["duration_s"].astype(float)),
        "cpu_pct_avg": df["cpu_pct_avg"].astype(float),
        "mem_mb": df["mem_kb_max"].astype(float)/1024,
        "hour": pd.to_datetime(df["timestamp"]).dt.hour,
        "dayofweek": pd.to_datetime(df["timestamp"]).dt.dayofweek,
        "tag_code": df["tag"].astype("category").cat.codes
    })
    # Scale
    scaler = joblib.load(RF_SCALER)
    return scaler.transform(feat)

def predict_rf():
    row = load_latest_log()
    X = extract_rf_features(row)
    rf = joblib.load(RF_MODEL)
    pred = rf.predict(X)[0]  # 1=pass, 0=fail
    return pred

def predict_lstm(pipeline_id):
    # Load all rows for this pipeline so far
    df = pd.read_csv("logs/ci_logs.csv")
    seq = df[df["pipeline_id"]==str(pipeline_id)].sort_values("timestamp")
    # Build the feature sequence
    Xs = seq[FEATURES].copy()
    Xs["log_duration"] = np.log1p(seq["duration_s"])
    Xs["mem_mb"] = seq["mem_kb_max"]/1024
    # Pick only seq_len rows
    arr = Xs.values
    if arr.shape[0] < SEQ_LEN:
        pad = np.zeros((SEQ_LEN-arr.shape[0], arr.shape[1]))
        arr = np.vstack([arr, pad])
    else:
        arr = arr[:SEQ_LEN]
    # Reshape for LSTM: (1, seq_len, n_features)
    arr = arr.reshape((1, SEQ_LEN, arr.shape[1]))
    lstm = load_model(LSTM_MODEL)
    prob = lstm.predict(arr)[0,0]
    return int(prob > 0.5)  # 1=pass, 0=fail

def run_and_heal(command, tag):
    # 1) Run the job & log it
    code = subprocess.call(f'python ci/ci_logger.py "{command}" --tag {tag}', shell=True)

    # 2) Stage-level RF check
    rf_pred = predict_rf()
    if rf_pred == 0:
        print("[RF] Anomaly detected—retrying job once")
        code = subprocess.call(command, shell=True)

    # 3) After lint stage, run LSTM checkpoint
    if tag == "lint":
        pipe_id = os.environ.get("CI_PIPELINE_ID")
        lstm_pred = predict_lstm(pipe_id)
        if lstm_pred == 0:
            print("[LSTM] Pipeline predicted to fail—aborting before test")
            sys.exit(0)

    return code

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("command", help="Shell command to execute")
    p.add_argument("--tag", required=True, help="Stage tag (build, lint, test)")
    args = p.parse_args()
    rc = run_and_heal(args.command, args.tag)
    sys.exit(rc)
