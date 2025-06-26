import pandas as pd

# 1) Load the merged logs
df = pd.read_csv("data/all_logs.csv")

# 2) Fill any missing mode with "baseline"
df["mode"] = df["mode"].fillna("baseline")

# (Optional) If you want to mark everything after a given date as ML:
# df.loc[pd.to_datetime(df["timestamp"]) >= "2025-06-24", "mode"] = "ml"

# 3) Save it back
df.to_csv("data/all_logs.csv", index=False)
print("✅ Backfilled mode – all rows now have a mode value")
