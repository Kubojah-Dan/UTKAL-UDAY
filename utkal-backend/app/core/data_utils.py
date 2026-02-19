import pandas as pd
import numpy as np
import os
from glob import glob

# Candidate names to look up in CSV headers (common variants)
_student_id_candidates = [
    'studentId', 'student_id', 'StudentId', 'user_id', 'userId',
    'anon_student_id', 'anon_id', 'ITEST_id', 'ITESTID', 'ITEST id',
    'itest_id', 'itestid', 'TEST_id', 'itest'
]
_skill_candidates = ['skill', 'skill_str', 'skill_id', 'problemId', 'problem_id', 'Problem Name', 'skill_name']
_starttime_candidates = ['startTime', 'start_time', 'timestamp', 'timeTaken', 'start', 'starttimestamp', 'StartTime']

def find_column(df, candidates):
    """Return the first matching column name from candidates present in df, else None."""
    for c in candidates:
        if c in df.columns:
            return c
    # try lowercase matching
    lower_map = {col.lower(): col for col in df.columns}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    return None

def read_and_concat_student_logs(raw_dir):
    files = sorted(glob(os.path.join(raw_dir, "student_log_*.csv")))
    if not files:
        raise FileNotFoundError(f"No files matching student_log_*.csv in {raw_dir}")
    dfs = []
    for f in files:
        print("Reading", f)
        # low_memory=False helps mixed dtypes
        df = pd.read_csv(f, low_memory=False)
        dfs.append(df)
    full = pd.concat(dfs, ignore_index=True)
    return full

def basic_cleaning(df):
    # Standardize column names: strip whitespace
    df.columns = [str(c).strip() for c in df.columns]

    # Coerce numeric columns, fill NaNs with median (robust)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Also try to detect numeric-like columns stored as object
    for c in df.columns:
        if c not in num_cols:
            # heuristic: a majority of values parse as numbers
            sample = df[c].dropna().astype(str).head(200)
            if len(sample) > 0:
                num_parsable = sum(1 for v in sample if _is_number_like(v))
                if num_parsable / len(sample) > 0.6:
                    num_cols.append(c)
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')
        median = df[c].median(skipna=True)
        if np.isnan(median):
            median = 0.0
        df[c] = df[c].fillna(median)

    return df

def _is_number_like(s):
    try:
        float(s)
        return True
    except:
        return False

def encode_skill_ids(df):
    # Detect skill column name
    skill_col = find_column(df, _skill_candidates)
    if skill_col is None:
        # make a synthetic skill column if none present
        print("Warning: no skill column detected. Creating synthetic single-skill column 'skill_unset'.")
        df['skill_unset'] = 'skill_unset'
        skill_col = 'skill_unset'
    df['skill_str'] = df[skill_col].astype(str)
    # create mapping preserving order of appearance
    uniq = list(dict.fromkeys(df['skill_str'].tolist()))
    skill_map = {s: i for i, s in enumerate(uniq)}
    df['skill_id'] = df['skill_str'].map(skill_map).astype(int)
    return df, skill_map

def create_sequence_features(df, max_seq_len=100):
    """
    Builds per-student sequences (list of dicts). Returns sequences as list of dicts:
    {'student_id': <id>, 'steps': [ {skill_id, correct, timeTaken, hintCount, ...}, ... ] }
    """
    # Auto-detect student id column
    student_col = find_column(df, _student_id_candidates)
    start_col = find_column(df, _starttime_candidates)

    print("Detected columns:")
    print("  student column:", student_col)
    print("  start/time column:", start_col)
    print("  skill column (internal): skill_id")

    # If student id not found, try fallback names or treat each row as unique student
    if student_col is None:
        print("Warning: no student id column detected. Will use synthetic student ids (row groups).")
        df['_student_synthetic'] = (df.index // 50).astype(str)  # group rows into synthetic students of 50 rows
        student_col = '_student_synthetic'

    # If start time not found, we'll rely on original row order
    if start_col is None:
        print("Warning: no start time column detected. Will use CSV order to sort interactions per student.")
        df['_order'] = np.arange(len(df))
        start_col = '_order'

    # Ensure 'correct' is present; if missing, try variations
    if 'correct' not in df.columns:
        alt_correct = None
        for cand in ['correct', 'is_correct', 'Correct', 'outcome', 'answer', 'original']:
            if cand in df.columns:
                alt_correct = cand
                break
        if alt_correct is None:
            print("Warning: no 'correct' column found. Assuming incorrect (0) for all rows.")
            df['correct'] = 0
        else:
            df['correct'] = df[alt_correct].apply(lambda x: 1 if (str(x).strip() in ['1','True','true','TRUE']) else 0)

    # Optional columns if exist
    for col in ['hintCount', 'hint_count', 'hints', 'hint']:
        if col in df.columns:
            df['hintCount'] = df[col].fillna(0).astype(float)
            break
    if 'hintCount' not in df.columns:
        df['hintCount'] = 0.0

    # timeTaken detect / normalize
    if 'timeTaken' not in df.columns:
        for col in ['timeTaken', 'time_taken', 'time', 'duration', 'timeSec']:
            if col in df.columns:
                df['timeTaken'] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                break
    if 'timeTaken' not in df.columns:
        df['timeTaken'] = 0.0

    # Ensure skill_id present
    if 'skill_id' not in df.columns:
        df, skill_map = encode_skill_ids(df)
    else:
        skill_map = None

    # Build sequences
    seqs = []
    # Sort by student & time
    df_sorted = df.sort_values([student_col, start_col])
    grouped = df_sorted.groupby(student_col, sort=False)
    for student, g in grouped:
        steps = []
        for _, row in g.iterrows():
            step = {
                'skill_id': int(row.get('skill_id', 0)),
                'correct': int(row.get('correct', 0)),
                'timeTaken': float(row.get('timeTaken', 0.0)),
                'hintCount': float(row.get('hintCount', 0.0)),
            }
            steps.append(step)
        if len(steps) >= 2:
            seqs.append({'student_id': str(student), 'steps': steps})
    return seqs
