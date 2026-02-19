import pandas as pd, glob
files = sorted(glob.glob("data/raw/student_log_*.csv"))
df = pd.read_csv(files[0], nrows=5)
print("Columns in first file:", df.columns.tolist())
# Show columns across all files (union)
cols = set()
for f in files:
    df = pd.read_csv(f, nrows=1)
    cols |= set(df.columns.tolist())
print("Union of columns across files:", sorted(list(cols)))

