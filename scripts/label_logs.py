import pandas as pd
import os

# Paths
INPUT_CSV  = "data/all_logs.csv"
OUTPUT_CSV = "data/all_logs_labeled.csv"

# Load
df = pd.read_csv(INPUT_CSV)

# Add label: success if exit_code==0, else failure
df['label'] = df['exit_code'].apply(lambda x: 'success' if x == 0 else 'failure')

# Save new file
df.to_csv(OUTPUT_CSV, index=False)
print(f"Labeled dataset saved to {OUTPUT_CSV}. Preview:")
print(df.head())
