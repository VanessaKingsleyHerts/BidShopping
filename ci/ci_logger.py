import csv
import shlex
import subprocess
import sys
import time
from datetime import datetime

import psutil
import os

# ensure logs/ folder exists
os.makedirs("logs", exist_ok=True)

def run_and_log(command_str, csv_path="logs/ci_logs.csv"):
    """
    Run the given shell command, measure duration, exit code, CPU and memory usage,
    and append a row to a CSV log.
    """
    # Prepare the CSV file and header if not exists
    header = [
        "timestamp",
        "command",
        "duration_s",
        "exit_code",
        "cpu_pct",
        "mem_kb",
    ]
    try:
        with open(csv_path, "r") as f:
            pass
    except FileNotFoundError:
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)

    args = shlex.split(command_str)
    start = time.time()
    proc = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr)

    # Record resource usage while running
    try:
        while proc.poll() is None:
            proc_cpu = psutil.cpu_percent(interval=0.5)
            proc_mem = psutil.Process(proc.pid).memory_info().rss / 1024
    except psutil.NoSuchProcess:
        proc_cpu = 0.0
        proc_mem = 0.0

    end = time.time()
    duration = round(end - start, 2)
    exit_code = proc.returncode

    # Write the results
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            command_str,
            duration,
            exit_code,
            proc_cpu,
            int(proc_mem),
        ])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ci/ci_logger.py '<command>'")
        sys.exit(1)

    run_and_log(sys.argv[1])
