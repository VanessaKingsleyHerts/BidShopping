import pandas as pd
import numpy as np

# Load original
df = pd.read_csv("data/all_logs.csv")

# How many synthetic copies per row?
N_DUPLICATES = 20

# Separate pass/fail
df_pass = df[df["status"] == "pass"]
df_fail = df[df["status"] == "fail"]

# Function to perturb features
def jitter(df, std=0.1):
    noisy = df.copy()
    for col in ["duration_s", "cpu_pct_avg", "mem_kb_max"]:
        noise = np.random.normal(loc=1.0, scale=std, size=len(df))
        noisy[col] = df[col] * noise
    return noisy

# Duplicate and perturb
aug_pass = pd.concat([jitter(df_pass) for _ in range(N_DUPLICATES)], ignore_index=True)
aug_fail = pd.concat([jitter(df_fail) for _ in range(N_DUPLICATES)], ignore_index=True)

# Combine and save
augmented = pd.concat([df, aug_pass, aug_fail], ignore_index=True)
augmented.to_csv("data/all_logs_aug.csv", index=False)
print("Saved augmented data to data/all_logs_aug.csv")
