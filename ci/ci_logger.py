# ci_logger.py

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

def run_and_log(command_str, csv_path="logs/ci_logs.csv", tag=None, label=None):
    """
    Run the given shell command, measure duration, exit code, CPU and memory usage,
    and append a row to a CSV log with both a stage tag and a status.

    Args:
        command_str (str): The shell command to execute.
        csv_path (str): Path to the CSV log file.
        tag (str): Stage tag for this run (e.g., 'build', 'lint', 'test').

    The CSV will have columns:
        timestamp, command, duration_s, exit_code, cpu_pct_avg, mem_kb_max, tag, status
    """
    header = [
        "timestamp",
        "command",
        "duration_s",
        "exit_code",
        "cpu_pct_avg",
        "mem_kb_max",
        "tag",
        "status"
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
    status = "pass" if exit_code == 0 else "fail"
    command = label if label else command_str

    # Write the results
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            command,
            duration,
            exit_code,
            avg_cpu,
            int(mem_max),
            tag,
            status,
            os.environ.get("CI_PIPELINE_ID", "unknown"),
            os.environ.get("HEAL_MODE", "baseline")
        ])

    sys.exit(exit_code)  # Important for CI systems


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a command and log performance.")
    parser.add_argument("command", help="Shell command to execute (quoted)")
    parser.add_argument("--tag", help="Stage tag for this run (e.g., build, lint, test)", required=False)
    parser.add_argument("--csv", help="Path to CSV log file", default="logs/ci_logs.csv")
    parser.add_argument("--label", help="Optional short name for command", required=False)

    args = parser.parse_args()
    run_and_log(args.command, args.csv, args.tag, args.label)
