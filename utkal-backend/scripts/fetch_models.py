import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.model_fetcher import download_missing_models

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download missing backend model artifacts.")
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Optional list of specific model filenames to download. If omitted, uses UTKAL_MODEL_FILES or default file list.",
    )
    args = parser.parse_args()

    if args.files:
        print("Warning: --files is not currently supported for custom filenames. Use UTKAL_MODEL_FILES environment variable.")

    print("Downloading missing model artifacts...")
    download_missing_models()
    print("Done. Missing model artifacts have been fetched if available.")
