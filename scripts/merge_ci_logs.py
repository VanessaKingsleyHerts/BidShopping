import pandas as pd, glob

files = glob.glob("data/raw/*.csv")
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
df.to_csv("data/all_logs.csv", index=False)
print(f"Merged {len(df)} rows into data/all_logs.csv")
