#!/usr/bin/env python3
import os, sys, csv, joblib, subprocess, argparse, shlex
import numpy as np
import pandas as pd
from keras.models import load_model

# os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Only show errors
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# Paths to models
RF_MODEL   = os.path.join(os.path.dirname(__file__), "../data/baseline/models/rf_model.joblib")
RF_SCALER  = os.path.join(os.path.dirname(__file__), "../data/baseline/models/rf_scaler.joblib")
LSTM_MODEL = os.path.join(os.path.dirname(__file__), "../data/baseline/models/lstm_model.keras")

# Constants
SEQ_LEN  = 2  # build + lint
FEATURES = ["log_duration", "cpu_pct_avg", "mem_mb", "tag_code"]
# include suite-level tags so RF retry can apply there too
RF_ELIGIBLE_TAGS = {"lint", "test", "unit", "functional"}

# Determine healing mode (baseline or ml) + selection policy
MODE = os.environ.get("HEAL_MODE", "none")
TEST_SELECTION_MODE = os.environ.get("TEST_SELECTION", "off").lower()  # off|suite|budget
MAX_TEST_MINUTES = float(os.environ.get("MAX_TEST_MINUTES", "15"))
RISK_THRESHOLD   = float(os.environ.get("RISK_THRESHOLD", "0.30"))

def _truthy(x):
    return str(x).strip().lower() in {"1","true","yes","y","on"}

def ensure_header(csv_path="logs/ci_logs.csv"):
    header = [
        "timestamp", "command", "duration_s", "exit_code",
        "cpu_pct_avg", "mem_kb_max", "tag", "status",
        "pipeline_id", "mode"
    ]
    if not os.path.exists(csv_path):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, "w", newline="") as f:
            csv.writer(f).writerow(header)

def load_latest_log():
    with open("logs/ci_logs.csv") as f:
        return list(csv.DictReader(f))[-1]

def extract_rf_features(row):
    df_row = pd.DataFrame([row])
    tag_map = {"build": 0, "lint": 1, "test": 2, "unit": 3, "functional": 4}
    feat = pd.DataFrame({
        "log_duration": np.log1p(df_row["duration_s"].astype(float)),
        "cpu_pct_avg": df_row["cpu_pct_avg"].astype(float),
        "mem_mb": df_row["mem_kb_max"].astype(float) / 1024,
        "hour": pd.to_datetime(df_row["timestamp"]).dt.hour,
        "dayofweek": pd.to_datetime(df_row["timestamp"]).dt.dayofweek,
        "tag_code": df_row["tag"].map(tag_map).fillna(-1).astype(int)
    })
    scaler = joblib.load(RF_SCALER)
    feat = feat[scaler.feature_names_in_]
    return scaler.transform(feat)

def predict_rf():
    row = load_latest_log()
    X = extract_rf_features(row)
    rf = joblib.load(RF_MODEL)
    return rf.predict(X)[0]  # 1 = pass, 0 = fail

def predict_lstm(pipeline_id):
    df_logs = pd.read_csv("logs/ci_logs.csv")
    seq = df_logs[df_logs["pipeline_id"] == str(pipeline_id)].sort_values("timestamp")
    if seq.empty:
        return 1  # no data, assume pass

    tag_map = {"build": 0, "lint": 1, "test": 2, "unit": 3, "functional": 4}
    feat_df = pd.DataFrame({
        "log_duration": np.log1p(seq["duration_s"].astype(float)),
        "cpu_pct_avg": seq["cpu_pct_avg"].astype(float),
        "mem_mb": seq["mem_kb_max"].astype(float) / 1024,
        "tag_code": seq["tag"].map(tag_map).fillna(-1).astype(int)
    })

    arr = feat_df.values
    if arr.shape[0] < SEQ_LEN:
        pad = np.zeros((SEQ_LEN - arr.shape[0], arr.shape[1]))
        arr = np.vstack([arr, pad])
    else:
        arr = arr[:SEQ_LEN]
    arr = arr.reshape((1, SEQ_LEN, arr.shape[1]))

    lstm = load_model(LSTM_MODEL)
    prob = lstm.predict(arr, verbose=0)[0, 0]
    return int(prob > 0.5)

def run_logged(command, tag, label=None, override_status=None):
    raw_code = subprocess.call(command, shell=True)

    status_flag = f"--force-status {override_status}" if override_status else ""
    log_cmd = f'python ci/ci_logger.py "{command}" --tag {tag} {status_flag}'
    if label:
        log_cmd += f' --label {label}'

    subprocess.call(log_cmd, shell=True)
    return raw_code

def run_and_heal(command, tag, label=None):
    ensure_header()

    # Initial execution
    init_code = run_logged(command, tag, label)

    # Injected failure (only if command initially passed)
    if _truthy(os.environ.get("INJECT_FAIL", "true")) and tag == "lint":
        if init_code == 0:
            print("[Injected Failure] Forcing artificial lint failure for baseline experiment")
            init_code = 1

    # Retry or abort logic
    if init_code != 0:
        if MODE == "baseline":
            print(f"[Baseline] {tag} failed — retrying once")
            return run_logged(command, tag, label)

        if MODE == "ml":
            if tag in RF_ELIGIBLE_TAGS and predict_rf() == 0:
                print(f"[RF] {tag} anomaly — retrying once")
                return run_logged(command, tag, label)

            if tag == "lint" and predict_lstm(os.getenv("CI_PIPELINE_ID", "0")) == 0:
                print("[LSTM] Pipeline predicted to fail — aborting before test")
                sys.exit(0)

    return init_code

# ───────── Suite selection helpers (unit / functional) ─────────
def soft_skip(tag, reason, label=None):
    """Log a 'skipped' row and exit 0 so the pipeline proceeds."""
    ensure_header()
    msg = f"skip:{tag}:{reason}"
    quoted_msg = shlex.quote(msg)
    log_cmd = f"python ci/ci_logger.py {quoted_msg} --tag {tag} --force-status skipped"
    if label:
        log_cmd += f" --label {label}"
    subprocess.call(log_cmd, shell=True)
    print(f"[Selector] Skipping suite '{tag}' — {reason}")
    return 0

def compute_suite_fail_rates():
    # % fails by tag from historical logs (ignores 'skipped')
    try:
        df = pd.read_csv("logs/ci_logs.csv")
    except Exception:
        return {"unit":0.0,"functional":0.0}
    df = df[df["tag"].isin(["unit","functional"])]
    df = df[df["status"].isin(["pass","fail"])]
    rates = {}
    for t,g in df.groupby("tag"):
        rates[t] = (g["status"].eq("fail").sum() / len(g)) if len(g) else 0.0
    for t in ["unit","functional"]:
        rates.setdefault(t, 0.0)
    return rates

def compute_suite_durations():
    # median minutes per suite from history
    default = 5.0
    try:
        df = pd.read_csv("logs/ci_logs.csv")
    except Exception:
        return {"unit":default,"functional":default}
    df = df[df["tag"].isin(["unit","functional"])]
    if df.empty:
        return {"unit":default,"functional":default}
    durs = {}
    for t,g in df.groupby("tag"):
        durs[t] = float(np.median(pd.to_numeric(g["duration_s"], errors="coerce").fillna(0.0))) / 60.0
    for t in ["unit","functional"]:
        durs.setdefault(t, default)
    return durs

def decide_suites_suite_mode(rates):
    # threshold policy; always include unit as a safety net
    selected = {"unit"}
    if rates.get("functional", 0.0) >= RISK_THRESHOLD:
        selected.add("functional")
    return selected

def decide_suites_budget_mode(rates, durs, budget):
    # greedy by (fail_rate / minutes)
    items = [((rates.get(t,0.0)/max(durs.get(t,5.0),0.1)), t) for t in ["unit","functional"]]
    items.sort(reverse=True)
    selected, used = set(), 0.0
    for _, t in items:
        m = durs.get(t, 5.0)
        if used + m <= budget:
            selected.add(t)
            used += m
    if not selected:
        selected.add("unit")
    print(f"[Selector] Budget={budget}m → {sorted(selected)} (≈{used:.1f}m)")
    return selected

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="Shell command to execute")
    parser.add_argument("--tag", required=True, help="Stage tag (build, lint) or suite tag (unit, functional)")
    parser.add_argument("--label", help="Optional short label for job")
    args = parser.parse_args()
    # Selection applies only to the suite jobs (requires YAML to tag suites as 'unit'/'functional')
    if TEST_SELECTION_MODE in {"suite","budget"} and args.tag in {"unit","functional"}:
        rates = compute_suite_fail_rates()
        chosen = (decide_suites_suite_mode(rates) if TEST_SELECTION_MODE == "suite"
                  else decide_suites_budget_mode(rates, compute_suite_durations(), MAX_TEST_MINUTES))
        print(f"[Selector] mode={TEST_SELECTION_MODE} tag={args.tag} rates={rates} chosen={sorted(chosen)}")
        if args.tag not in chosen:
            sys.exit(soft_skip(args.tag, f"Not selected ({TEST_SELECTION_MODE})", args.label))
    sys.exit(run_and_heal(args.command, args.tag, args.label))
