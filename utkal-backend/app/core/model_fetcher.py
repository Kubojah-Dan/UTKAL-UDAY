import gzip
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = BACKEND_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL_FILES: List[str] = [
    "quest2skill.json",
    "dkt_xes3g5m.pt",
    "temporal_lstm.pt",
    "dkt_xes3g5m_meta.json",
    "bkt_params_xes3g5m.json",
]

DEFAULT_BASE_URL = os.getenv("UTKAL_MODEL_BASE_URL", "")


def _build_file_urls(base_url: str, filenames: Iterable[str]) -> Dict[str, str]:
    base = base_url.strip()
    if not base:
        raise ValueError("UTKAL_MODEL_BASE_URL is not configured")
    if not base.endswith("/"):
        base += "/"
    return {filename: base + filename for filename in filenames}


def _download_file(url: str, dest: Path) -> None:
    """Download file from URL, automatically decompressing .gz files."""
    request = Request(url, headers={"User-Agent": "UtkalModelFetcher/1.0"})
    try:
        with urlopen(request) as response:
            data = response.read()
            
        # If URL ends with .gz, decompress and save without .gz extension
        if url.endswith('.gz'):
            try:
                decompressed = gzip.decompress(data)
                # Remove .gz from filename
                final_dest = Path(str(dest).rsplit('.gz', 1)[0])
                with open(final_dest, "wb") as out_file:
                    out_file.write(decompressed)
                print(f"[model_fetcher] Decompressed {dest.name} → {final_dest.name}")
            except Exception as exc:
                raise RuntimeError(f"Failed to decompress {url}: {exc}")
        else:
            with open(dest, "wb") as out_file:
                out_file.write(data)
                
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error downloading {url}: {exc.code} {exc.reason}")
    except URLError as exc:
        raise RuntimeError(f"URL error downloading {url}: {exc.reason}")


def _read_env_file_list(env_name: str, default: List[str]) -> List[str]:
    raw = os.getenv(env_name, "")
    if not raw:
        return default
    try:
        return json.loads(raw) if raw.strip().startswith("[") else [p.strip() for p in raw.split(",") if p.strip()]
    except Exception:
        return [p.strip() for p in raw.split(",") if p.strip()]


def get_model_files() -> List[str]:
    return _read_env_file_list("UTKAL_MODEL_FILES", DEFAULT_MODEL_FILES)


def _missing_model_files() -> List[str]:
    """Check which model files are missing (uncompressed OR compressed versions)."""
    missing = []
    for filename in get_model_files():
        uncompressed_path = MODELS_DIR / filename
        compressed_path = MODELS_DIR / f"{filename}.gz"
        # File is considered present if either version exists
        if not uncompressed_path.exists() and not compressed_path.exists():
            missing.append(filename)
    return missing


def download_missing_models() -> None:
    base_url = os.getenv("UTKAL_MODEL_BASE_URL", "").strip()
    if not base_url:
        raise RuntimeError("UTKAL_MODEL_BASE_URL must be set to download model artifacts")
    missing_files = _missing_model_files()
    if not missing_files:
        print("[model_fetcher] No missing model files detected.")
        return

    # Try to download with .gz extension first, fall back to uncompressed
    urls = _build_file_urls(base_url, missing_files)
    for filename, url in urls.items():
        # Try .gz first, then without
        url_gz = f"{url}.gz"
        destination = MODELS_DIR / filename
        
        # Check if .gz version exists on server
        try:
            print(f"[model_fetcher] Attempting to download {filename}.gz from {url_gz}...")
            _download_file(url_gz, destination)
            print(f"[model_fetcher] Successfully downloaded and decompressed {filename}")
        except RuntimeError as gz_error:
            # If .gz fails, try uncompressed
            try:
                print(f"[model_fetcher] .gz not available, trying uncompressed: {filename}")
                _download_file(url, destination)
                print(f"[model_fetcher] Saved {filename} to {destination}")
            except RuntimeError as uncompressed_error:
                print(f"[model_fetcher] ERROR: Failed to download {filename}: {uncompressed_error}")
                raise RuntimeError(f"Could not download {filename} in any format") from uncompressed_error


def ensure_models_available() -> None:
    missing_files = _missing_model_files()
    if not missing_files:
        return
    if os.getenv("UTKAL_MODEL_DOWNLOAD_ENABLED", "false").strip().lower() not in {"1", "true", "yes", "on"}:
        raise RuntimeError(
            f"Missing model files: {missing_files}. Set UTKAL_MODEL_DOWNLOAD_ENABLED=true and UTKAL_MODEL_BASE_URL to auto-download them."
        )
    download_missing_models()
