#!/usr/bin/env python3
import os
import sys
import pandas as pd
from datetime import datetime

IN_CSV  = "data/all_logs.csv"
OUT_CSV = "data/healing_outcomes.csv"

def main():
    if not os.path.exists(IN_CSV):
        print(f"⚠️ {IN_CSV} not found; nothing to compute.")
        sys.exit(0)

    df = pd.read_csv(IN_CSV)
    # expected columns per your logger/schema
    needed = {"timestamp","command","duration_s","exit_code","cpu_pct_avg","mem_kb_max","tag","status","pipeline_id","mode"}
    missing = needed - set(df.columns)
    if missing:
        print(f"❌ Missing columns in {IN_CSV}: {missing}")
        sys.exit(1)

    # Normalize types
    df["timestamp"]   = pd.to_datetime(df["timestamp"], errors="coerce")
    df["pipeline_id"] = df["pipeline_id"].astype(str)
    df["tag"]         = df["tag"].astype(str)
    df["mode"]        = df["mode"].astype(str).str.lower()
    df = df.sort_values(["pipeline_id","timestamp"])

    # Helper: does pipeline contain any 'test' stage after lint?
    def has_test_after(group, lint_time):
        later = group[group["timestamp"] > lint_time]
        return (later["tag"] == "test").any() or (later["tag"] == "unit").any() or (later["tag"] == "functional").any()

    records = []

    for pid, g in df.groupby("pipeline_id", sort=False):
        # detect LSTM abort (ml mode, lint fail, no later tests)
        lint_fails = g[(g["tag"]=="lint") & (g["status"]=="fail")]
        for _, lf in lint_fails.iterrows():
            if (lf.get("mode","").lower() == "ml") and not has_test_after(g, lf["timestamp"]):
                records.append({
                    "timestamp": lf["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "tag": "lint",
                    "mode": "ml",
                    "action": "lstm-abort",
                    "result": "aborted"
                })

        # stage-level retries & proceeds (build/lint/test/unit/functional)
        for tag, sg in g.groupby("tag"):
            # skip rows (soft skip from test selection)
            skipped = sg[sg["status"]=="skipped"]
            for _, sk in skipped.iterrows():
                records.append({
                    "timestamp": sk["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "tag": tag,
                    "mode": (sk.get("mode") or "").lower() or "none",
                    "action": "skip",
                    "result": "skipped"
                })

            # non-skipped attempts
            attempts = sg[sg["status"].isin(["pass","fail"])].sort_values("timestamp")
            if attempts.empty:
                continue

            # retry if more than one attempt for this (pid, tag)
            if len(attempts) > 1:
                final = attempts.iloc[-1]
                records.append({
                    "timestamp": final["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "tag": tag,
                    "mode": (final.get("mode") or "").lower() or "none",
                    "action": "retry",
                    "result": final["status"]
                })
            else:
                only = attempts.iloc[0]
                records.append({
                    "timestamp": only["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "tag": tag,
                    "mode": (only.get("mode") or "").lower() or "none",
                    "action": "proceed",
                    "result": only["status"]
                })

    if not records:
        print("ℹ️ No outcome records to write.")
        sys.exit(0)

    out = pd.DataFrame.from_records(records).sort_values("timestamp")
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"✅ Wrote {len(out)} rows → {OUT_CSV}")

if __name__ == "__main__":
    main()

# local test:
# python scripts/merge_incremental.py
# python scripts/compute_healing_outcomes.py
# inspect
# head -n 20 data/healing_outcomes.csv
