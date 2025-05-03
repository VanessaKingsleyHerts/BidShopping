# ci/ci_logger.py

import csv
import os
import shlex
import subprocess
import sys
import time

import psutil  # add to your requirements.txt

def measure_and_log(cmd, csv_path="logs/ci_logs.csv"):
    # ensure logs folder exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # record start
    start_ts = time.time()

    # run the command
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    retcode = proc.returncode

    # record end + metrics
    end_ts = time.time()
    duration = end_ts - start_ts

    # snapshot resource usage of this process
    p = psutil.Process(proc.pid)
    with p.oneshot():
        cpu = p.cpu_percent(interval=None)
        mem = p.memory_info().rss // 1024  # in KB

    # prepare line
    headers = ["timestamp","command","duration_s","exit_code","cpu_pct","mem_kb"]
    row = [time.strftime("%Y-%m-%d %H:%M:%S"),
           cmd,
           f"{duration:.2f}",
           str(retcode),
           f"{cpu:.1f}",
           str(mem)]

    # write header if needed + append row
    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(headers)
        writer.writerow(row)

    # emit stdout/stderr for CI logs
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    return retcode

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ci/ci_logger.py \"<command>\"")
        sys.exit(1)
    cmd = sys.argv[1]
    exit(sys.measure_and_log(cmd))
