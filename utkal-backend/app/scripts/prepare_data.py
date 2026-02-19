import os
import argparse
from app.core.data_utils import read_and_concat_student_logs, basic_cleaning, encode_skill_ids, create_sequence_features
import pandas as pd
import pickle

def main(raw_dir, processed_dir):
    os.makedirs(processed_dir, exist_ok=True)
    print("Reading and concatenating student logs...")
    df = read_and_concat_student_logs(raw_dir)
    print("Raw shape:", df.shape)
    print("Basic cleaning...")
    df = basic_cleaning(df)
    print("Encoding skills...")
    df, skill_map = encode_skill_ids(df)
    print(f"Unique skills: {len(skill_map)}")
    print("Saving cleaned combined CSV...")
    combined_csv = os.path.join(processed_dir, "combined_cleaned.csv")
    df.to_csv(combined_csv, index=False)
    print("Creating sequences...")
    seqs = create_sequence_features(df)
    print("Number of student sequences:", len(seqs))
    # Save sequences to pickle for training script
    with open(os.path.join(processed_dir, "sequences.pkl"), "wb") as f:
        pickle.dump({'sequences': seqs, 'skill_map': skill_map}, f)
    print("Saved processed data to", processed_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_dir", default="data/raw", help="Folder with student_log_*.csv")
    parser.add_argument("--processed_dir", default="data/processed", help="Folder to write cleaned files")
    args = parser.parse_args()
    main(args.raw_dir, args.processed_dir)
