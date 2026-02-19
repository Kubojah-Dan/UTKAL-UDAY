import json, os, subprocess, tempfile, logging, time
from collections import defaultdict
from typing import List

logger = logging.getLogger("distill")
BKT_FILE = "app/models/bkt_params.json"
BKT_STATS = "app/models/bkt_stats.json"
LOG_CSV = "app/data/logs.csv"

def append_logs_to_csv(interactions, student_id=None):
    # interactions: list of objects with quest_id, skill_id (optional), timestamp, outcome
    os.makedirs(os.path.dirname(LOG_CSV), exist_ok=True)
    with open(LOG_CSV, "a+", encoding="utf8") as f:
        for it in interactions:
            skill = getattr(it, "skill_id", None) or getattr(it, "skill", None) or ""
            f.write(f"{student_id},{it.quest_id},{skill},{it.timestamp},{int(it.outcome)}\n")

def update_aggregated_stats(interactions):
    # keep counts per skill: attempts, corrects
    stats = {}
    if os.path.exists(BKT_STATS):
        with open(BKT_STATS,"r",encoding="utf8") as f:
            stats = json.load(f)
    else:
        stats = {}
    for it in interactions:
        skill = str(getattr(it,"skill_id", "") or getattr(it,"skill",""))
        if not skill:
            continue
        st = stats.get(skill, {"attempts":0, "correct":0})
        st["attempts"] += 1
        st["correct"] += int(bool(it.outcome))
        stats[skill] = st
    with open(BKT_STATS,"w",encoding="utf8") as f:
        json.dump(stats,f,indent=2)
    logger.info("Updated aggregated stats for %d skills", len(stats))
    return stats

def quick_params_from_stats(stats):
    # simple heuristic MLE for guess/slip (very rough)
    out = {}
    for skill, st in stats.items():
        attempts = st.get("attempts",1)
        correct = st.get("correct",0)
        p_obs = correct/attempts
        # rough defaults — these are placeholders until EM runs
        p_guess = max(0.01, min(0.5, 1 - p_obs))  # naive
        p_slip = max(0.01, min(0.5, 1 - p_obs))
        out[skill] = {"p_init": p_obs*0.5 + 0.1, "p_trans": 0.01, "p_guess": p_guess, "p_slip": p_slip}
    return out

def compute_bkt_updates(interactions, student_id=None) -> dict:
    """
    Called from /sync. Returns a small set of updates the server will send back to the client.
    We'll:
      - append to logs.csv
      - update aggregated stats
      - return quick params for any skills seen
    For production: schedule offline EM (weekly) to re-run and overwrite app/models/bkt_params.json
    """
    append_logs_to_csv(interactions, student_id=student_id)
    stats = update_aggregated_stats(interactions)
    # produce quick params for skills present in this batch
    skills_in_batch = set()
    for it in interactions:
        skill = str(getattr(it,"skill_id","") or getattr(it,"skill",""))
        if skill:
            skills_in_batch.add(skill)
    bkt_updates = {}
    quick = quick_params_from_stats(stats)
    for s in skills_in_batch:
        if s in quick:
            bkt_updates[s] = quick[s]
    # Also, optionally, merge with existing BKT_FILE for fallback
    if os.path.exists(BKT_FILE):
        with open(BKT_FILE,"r",encoding="utf8") as f:
            cur = json.load(f)
        for s, params in bkt_updates.items():
            # if we have full params from BKT_FILE prefer them
            curp = cur.get(str(s))
            if curp:
                bkt_updates[s].update(curp)
    return bkt_updates

def run_offline_em(sequences_pkl="data/processed/sequences.pkl", out_json=BKT_FILE, max_iter=50):
    """
    Invokes your EM script (app.core.bkt_em) to compute final BKT params.
    It runs as a subprocess and writes to out_json atomically.
    """
    logger.info("Starting offline EM distillation...")
    # call the module you used earlier
    cmd = ["python","-m","app.core.bkt_em", sequences_pkl, "--out", out_json + ".tmp", "--max_iter", str(max_iter)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error("EM failed: %s\nstdout:%s\nstderr:%s", res.returncode, res.stdout, res.stderr)
        raise RuntimeError("EM failed")
    os.replace(out_json + ".tmp", out_json)
    logger.info("EM finished, updated %s", out_json)

