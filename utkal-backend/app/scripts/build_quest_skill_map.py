import csv
import json
import os
import argparse
import logging
import glob
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_map")

SKILL_REGISTRY_PATH = "app/models/skill_registry.json"


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def load_or_create(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)
    return {}


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def _normalize_row(row):
    """Normalize CSV DictReader row keys and values."""
    new = {}
    for k, v in row.items():
        if k is None:
            continue
        new[k.strip()] = v if v is not None else ""
    return new


def expand_input_patterns(patterns):
    """Expand wildcard patterns (Windows-safe)."""
    files = []
    for p in patterns:
        matches = glob.glob(p)
        if not matches:
            logger.warning("Pattern did not match any files: %s", p)
        files.extend(matches)

    files = sorted(set(files))
    if not files:
        raise FileNotFoundError("No CSV files found for the given --raw_csv patterns.")
    return files


# ------------------------------------------------------------
# Main Logic
# ------------------------------------------------------------

def build_map(
    csv_patterns,
    out_json="app/models/quest2skill.json",
    report="app/models/unmapped_report.csv"
):
    csv_files = expand_input_patterns(csv_patterns)
    logger.info("Found %d CSV files to process", len(csv_files))

    # Load or create persistent skill registry
    skill_registry = load_or_create(SKILL_REGISTRY_PATH)
    next_skill_id = max(skill_registry.values(), default=0) + 1

    # Indexes
    by_problem, by_assist, by_skill = {}, {}, {}
    rows = []

    # Read CSVs
    for p in csv_files:
        logger.info("Reading CSV: %s", p)
        with open(p, "r", encoding="utf8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(_normalize_row(r))

    if not rows:
        logger.warning("No rows loaded from input CSVs.")

    # --------------------------------------------------------
    # Register skills (persistent numeric IDs)
    # --------------------------------------------------------

    for r in rows:
        skill_str = (r.get("skill_str") or r.get("skill") or "").strip()
        if skill_str:
            if skill_str not in skill_registry:
                skill_registry[skill_str] = next_skill_id
                next_skill_id += 1

    # Persist registry immediately
    save_json(SKILL_REGISTRY_PATH, skill_registry)
    logger.info("Skill registry size: %d", len(skill_registry))

    # --------------------------------------------------------
    # Build candidate lookup tables
    # --------------------------------------------------------

    for r in rows:
        problem_id = r.get("problemId") or r.get("actionId")
        assist_id = r.get("assistmentId")
        skill_str = (r.get("skill_str") or r.get("skill") or "").strip()

        skill_id = skill_registry.get(skill_str)

        if problem_id:
            by_problem[str(problem_id)] = {
                "skill_str": skill_str,
                "skill_id": skill_id,
            }

        if assist_id:
            by_assist[str(assist_id)] = {
                "skill_str": skill_str,
                "skill_id": skill_id,
            }

        if skill_str:
            by_skill[skill_str] = {
                "skill_str": skill_str,
                "skill_id": skill_id,
            }

    # --------------------------------------------------------
    # Build final quest → skill map
    # --------------------------------------------------------

    out = {}
    unmapped = defaultdict(int)

    for r in rows:
        quest_key = (
            r.get("actionId")
            or r.get("problemId")
            or f"row{abs(hash(json.dumps(r, sort_keys=True))) % 100000000}"
        )
        quest_key = str(quest_key)

        if quest_key in out:
            continue

        mapped = None

        # Exact matches
        pid = r.get("problemId") or r.get("actionId")
        aid = r.get("assistmentId")
        skill_candidate = (r.get("skill_str") or r.get("skill") or "").strip()

        if pid and str(pid) in by_problem:
            mapped = by_problem[str(pid)]
        elif aid and str(aid) in by_assist:
            mapped = by_assist[str(aid)]
        elif skill_candidate and skill_candidate in by_skill:
            mapped = by_skill[skill_candidate]
        else:
            # Fuzzy match
            if skill_candidate:
                best = ("", 0.0)
                for k in by_skill:
                    sim = similar(skill_candidate.lower(), k.lower())
                    if sim > best[1]:
                        best = (k, sim)
                if best[1] > 0.75:
                    mapped = by_skill.get(best[0])

        if mapped is None:
            unmapped[quest_key] += 1
            out[quest_key] = {
                "problemId": r.get("problemId"),
                "assistmentId": r.get("assistmentId"),
                "skill_str": skill_candidate,
                "skill_id": None,
            }
        else:
            out[quest_key] = {
                "problemId": r.get("problemId"),
                "assistmentId": r.get("assistmentId"),
                "skill_str": mapped.get("skill_str"),
                "skill_id": mapped.get("skill_id"),
            }

    # --------------------------------------------------------
    # Write outputs
    # --------------------------------------------------------

    save_json(out_json, out)

    os.makedirs(os.path.dirname(report), exist_ok=True)
    with open(report, "w", encoding="utf8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["quest_key", "problemId", "assistmentId", "skill_str", "skill_id"])
        for k, v in out.items():
            writer.writerow([
                k,
                v.get("problemId"),
                v.get("assistmentId"),
                (v.get("skill_str") or "").replace(",", " "),
                v.get("skill_id"),
            ])

    num_unmapped = sum(1 for v in out.values() if v["skill_id"] is None)

    logger.info("Saved %d quest mappings → %s", len(out), out_json)
    logger.info("Unmapped quests: %d → %s", num_unmapped, report)
    logger.info("Skill registry: %s", SKILL_REGISTRY_PATH)


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw_csv",
        nargs="+",
        required=True,
        help="input csv(s) or wildcard patterns e.g. data/raw/student_log_*.csv",
    )
    parser.add_argument(
        "--out",
        default="app/models/quest2skill.json",
        help="output JSON path",
    )
    parser.add_argument(
        "--report",
        default="app/models/unmapped_report.csv",
        help="unmapped CSV report path",
    )
    args = parser.parse_args()

    build_map(args.raw_csv, out_json=args.out, report=args.report)
