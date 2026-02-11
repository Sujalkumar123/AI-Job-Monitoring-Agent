import pandas as pd
import os

csv_path = r'c:\Users\Sujal kumar\OneDrive\Desktop\Job_scrapper AI\output\jobs_data.csv'

if not os.path.exists(csv_path):
    print(f"File not found: {csv_path}")
else:
    try:
        df = pd.read_csv(csv_path)
        print(f"Total rows: {len(df)}")
        print("-" * 30)
        print("Columns:")
        print(list(df.columns))
        print("-" * 30)
        print("Platform counts:")
        print(df["Platform Source"].value_counts())
        print("-" * 30)
        print("Category counts:")
        print(df["Posting Category"].value_counts())
        print("-" * 30)
        print("First 5 rows:")
        print(df.head(5).to_string())
    except Exception as e:
        print(f"Error reading CSV: {e}")
