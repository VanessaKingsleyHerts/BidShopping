import csv
import shlex
import subprocess
import sys
import time
from datetime import datetime
import psutil
import os
import argparse

# Ensure logs/ folder exists
os.makedirs("logs", exist_ok=True)

def run_and_log(command_str, csv_path="logs/ci_logs.csv", tag=None):
    """
    Run the given shell command, measure duration, exit code, CPU and memory usage,
    and append a row to a CSV log.
    """
    header = [
        "timestamp",
        "command",
        "duration_s",
        "exit_code",
        "cpu_pct_avg",
        "mem_kb_max",
        "tag"
    ]

    # Initialize CSV if it doesn't exist
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)

    args = shlex.split(command_str)
    start = time.time()
    proc = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr)

    cpu_samples = []
    mem_max = 0

    try:
        while proc.poll() is None:
            cpu = psutil.cpu_percent(interval=0.5)
            cpu_samples.append(cpu)

            try:
                mem = psutil.Process(proc.pid).memory_info().rss / 1024  # in KB
                mem_max = max(mem_max, mem)
            except psutil.NoSuchProcess:
                break
    except psutil.NoSuchProcess:
        pass

    end = time.time()
    duration = round(end - start, 2)
    exit_code = proc.returncode
    avg_cpu = round(sum(cpu_samples) / len(cpu_samples), 2) if cpu_samples else 0.0
    tag = "success" if exit_code == 0 else "failure"

    # Write the results
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            command_str,
            duration,
            exit_code,
            avg_cpu,
            int(mem_max),
            tag
        ])

    sys.exit(exit_code)  # Important for CI systems


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a command and log performance.")
    parser.add_argument("command", help="Shell command to execute (quoted)")
    parser.add_argument("--tag", help="Optional tag or label for this run", default=None)
    parser.add_argument("--csv", help="Path to CSV log file", default="logs/ci_logs.csv")

    args = parser.parse_args()
    run_and_log(args.command, args.csv, args.tag)
