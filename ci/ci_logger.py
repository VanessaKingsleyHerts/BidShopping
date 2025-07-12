#!/usr/bin/env python3

import csv
import shlex
import subprocess
import sys
import time
from datetime import datetime
import psutil
import os
import argparse
from ci.log_schema import EXPECTED_COLS as HEADER

# Ensure logs/ folder exists
os.makedirs("logs", exist_ok=True)

def run_and_log(command_str, csv_path="logs/ci_logs.csv", tag=None, label=None, force_status=None):
    """
    Run a shell command, measure duration, CPU, memory usage, and log results.
    """
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="") as f:
            csv.writer(f).writerow(HEADER)

    args = shlex.split(command_str)
    start = time.time()
    proc = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr)

    cpu_samples = []
    mem_max = 0
    try:
        p = psutil.Process(proc.pid)
    except psutil.NoSuchProcess:
        p = None

    try:
        while proc.poll() is None:
            cpu_samples.append(psutil.cpu_percent(interval=0.5))
            if p:
                try:
                    mem_kb = p.memory_info().rss / 1024
                    mem_max = max(mem_max, mem_kb)
                except psutil.NoSuchProcess:
                    break
    except psutil.NoSuchProcess:
        pass

    duration = round(time.time() - start, 2)
    exit_code = proc.returncode
    avg_cpu = round(sum(cpu_samples) / len(cpu_samples), 2) if cpu_samples else 0.0
    status = force_status if force_status else ("pass" if exit_code == 0 else "fail")
    command = label if label else command_str

    row = [
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        command,
        duration,
        exit_code,
        avg_cpu,
        int(mem_max),
        tag,
        status,
        os.environ.get("CI_PIPELINE_ID", "unknown"),
        os.environ.get("HEAL_MODE", "ml")
    ]

    with open(csv_path, "a", newline="") as f:
        csv.writer(f).writerow(row)

    sys.exit(exit_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="Shell command to execute (quoted)")
    parser.add_argument("--tag", required=False)
    parser.add_argument("--csv", default="logs/ci_logs.csv")
    parser.add_argument("--label", required=False)
    parser.add_argument("--force-status", default=None)
    args = parser.parse_args()

    run_and_log(args.command, args.csv, args.tag, args.label, args.force_status)
