import json
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import torch
    import torch.nn as nn
except Exception:  # pragma: no cover - graceful fallback when torch is unavailable
    torch = None
    nn = None

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models"
DKT_MODEL_FILE = MODELS_DIR / "dkt_xes3g5m.pt"
DKT_META_FILE = MODELS_DIR / "dkt_xes3g5m_meta.json"
BKT_XES_FILE = MODELS_DIR / "bkt_params_xes3g5m.json"
BKT_FALLBACK_FILE = MODELS_DIR / "bkt_params.json"

_XES_NUMERIC_PATTERN = re.compile(r"^XES-(\d+)$", re.IGNORECASE)


def _safe_int(value, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _safe_float(value, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _normalize_question_key(question_id: object) -> str:
    raw = str(question_id or "").strip()
    if not raw:
        return ""
    match = _XES_NUMERIC_PATTERN.match(raw)
    if match:
        return match.group(1)
    return raw


def _record_timestamp(row: Dict) -> int:
    ts = _safe_int(row.get("timestamp"), 0)
    if ts < 10_000_000_000:
        return ts * 1000
    return ts


def _posterior_after_observation(mastery: float, correct: bool, guess: float, slip: float) -> float:
    if correct:
        numer = mastery * (1.0 - slip)
        denom = numer + (1.0 - mastery) * guess
    else:
        numer = mastery * slip
        denom = numer + (1.0 - mastery) * (1.0 - guess)
    if denom <= 1e-9:
        return mastery
    return max(0.0, min(1.0, numer / denom))


def _bkt_posterior(outcomes: Iterable[bool], params: Dict) -> float:
    p = _safe_float(params.get("p_init"), 0.25)
    p_trans = _safe_float(params.get("p_trans"), 0.08)
    p_guess = _safe_float(params.get("p_guess"), 0.2)
    p_slip = _safe_float(params.get("p_slip"), 0.1)

    p = max(1e-6, min(1.0 - 1e-6, p))
    p_trans = max(1e-6, min(1.0 - 1e-6, p_trans))
    p_guess = max(1e-6, min(0.49, p_guess))
    p_slip = max(1e-6, min(0.49, p_slip))

    for outcome in outcomes:
        p = _posterior_after_observation(p, bool(outcome), p_guess, p_slip)
        p = p + (1.0 - p) * p_trans
    return max(0.0, min(1.0, p))


if nn is not None:  # pragma: no cover - tiny wrapper around torch module
    class DKTSequenceModel(nn.Module):
        def __init__(
            self,
            num_questions: int,
            num_concepts: int,
            q_emb_dim: int,
            c_emb_dim: int,
            hidden_dim: int,
            num_layers: int,
            dropout: float,
        ):
            super().__init__()
            self.question_emb = nn.Embedding(num_questions + 1, q_emb_dim, padding_idx=0)
            self.concept_emb = nn.Embedding(num_concepts + 1, c_emb_dim, padding_idx=0)
            self.correct_emb = nn.Embedding(2, 8)
            self.delta_fc = nn.Linear(1, 8)
            self.dropout = nn.Dropout(dropout)

            input_dim = q_emb_dim + c_emb_dim + 8 + 8
            self.gru = nn.GRU(
                input_size=input_dim,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0.0,
            )
            self.head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim // 2, 1),
            )

        def forward(self, q_ids, c_ids, correct_ids, delta_times):
            qv = self.question_emb(q_ids)
            cv = self.concept_emb(c_ids)
            rv = self.correct_emb(correct_ids)
            dv = torch.tanh(self.delta_fc(delta_times.unsqueeze(-1)))
            features = torch.cat([qv, cv, rv, dv], dim=-1)
            features = self.dropout(features)
            hidden, _ = self.gru(features)
            logits = self.head(hidden).squeeze(-1)
            return torch.sigmoid(logits)
else:
    DKTSequenceModel = None


@lru_cache(maxsize=1)
def _load_dkt_metadata() -> Dict:
    if not DKT_META_FILE.exists():
        return {}
    try:
        return json.loads(DKT_META_FILE.read_text(encoding="utf8"))
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _load_bkt_params() -> Dict:
    src = BKT_XES_FILE if BKT_XES_FILE.exists() else BKT_FALLBACK_FILE
    if not src.exists():
        return {}
    try:
        return json.loads(src.read_text(encoding="utf8"))
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _load_dkt_model():
    if torch is None or nn is None:
        return None
    if DKTSequenceModel is None:
        return None
    if not DKT_MODEL_FILE.exists():
        return None

    meta = _load_dkt_metadata()
    if not meta:
        return None

    cfg = meta.get("dkt_config") or {}
    num_questions = _safe_int(cfg.get("num_questions"), 0)
    num_concepts = _safe_int(cfg.get("num_concepts"), 0)
    if num_questions <= 0 or num_concepts <= 0:
        return None

    model = DKTSequenceModel(
        num_questions=num_questions,
        num_concepts=num_concepts,
        q_emb_dim=_safe_int(cfg.get("question_embedding_dim"), 64),
        c_emb_dim=_safe_int(cfg.get("concept_embedding_dim"), 32),
        hidden_dim=_safe_int(cfg.get("hidden_dim"), 128),
        num_layers=_safe_int(cfg.get("num_layers"), 2),
        dropout=_safe_float(cfg.get("dropout"), 0.2),
    )
    state = torch.load(DKT_MODEL_FILE, map_location="cpu")
    model.load_state_dict(state, strict=False)
    model.eval()
    return model


def _resolve_concept_for_record(row: Dict, meta: Dict) -> str:
    q_key = _normalize_question_key(row.get("problem_id") or row.get("quest_id"))
    q_to_c = meta.get("question_to_primary_concept") or {}
    if q_key and q_key in q_to_c:
        return str(q_to_c[q_key])

    skill_id = str(row.get("skill_id") or "").strip()
    if skill_id:
        return skill_id
    return "unknown"


def estimate_skill_mastery(records: List[Dict]) -> Dict[str, float]:
    if not records:
        return {}

    meta = _load_dkt_metadata()
    grouped: Dict[str, List[Tuple[int, bool]]] = defaultdict(list)
    for row in records:
        concept_key = _resolve_concept_for_record(row, meta)
        grouped[concept_key].append((_record_timestamp(row), bool(row.get("outcome"))))

    params_map = _load_bkt_params()
    out: Dict[str, float] = {}
    for concept_key, seq in grouped.items():
        seq_sorted = [flag for _, flag in sorted(seq, key=lambda x: x[0])]
        params = params_map.get(str(concept_key)) or params_map.get(str(concept_key).lower()) or {
            "p_init": 0.25,
            "p_trans": 0.08,
            "p_guess": 0.2,
            "p_slip": 0.1,
        }
        out[concept_key] = _bkt_posterior(seq_sorted, params)
    return out


def estimate_dkt_next_correct(records: List[Dict]) -> Optional[float]:
    if not records:
        return None
    model = _load_dkt_model()
    meta = _load_dkt_metadata()
    if model is None or not meta or torch is None:
        return None

    q_map = meta.get("question_to_idx") or {}
    c_map = meta.get("concept_to_idx") or {}
    q_to_c = meta.get("question_to_primary_concept") or {}
    max_seq_len = _safe_int(meta.get("dkt_config", {}).get("max_seq_len"), 200)
    default_concept = _safe_int(c_map.get("unknown"), 0)

    sorted_rows = sorted(records, key=_record_timestamp)
    q_ids: List[int] = []
    c_ids: List[int] = []
    r_ids: List[int] = []
    d_ts: List[float] = []

    prev_ts = None
    for row in sorted_rows:
        q_key = _normalize_question_key(row.get("problem_id") or row.get("quest_id"))
        q_idx = _safe_int(q_map.get(q_key), 0)
        concept_key = str(q_to_c.get(q_key) or row.get("skill_id") or "unknown")
        c_idx = _safe_int(c_map.get(concept_key), default_concept)
        r_idx = 1 if bool(row.get("outcome")) else 0

        now = _record_timestamp(row)
        if prev_ts is None:
            delta = 0.0
        else:
            delta = max(0.0, (now - prev_ts) / 1000.0)
        prev_ts = now

        q_ids.append(q_idx)
        c_ids.append(c_idx)
        r_ids.append(r_idx)
        d_ts.append(min(delta, 3600.0))

    if len(q_ids) < 2:
        return None

    q_ids = q_ids[-max_seq_len:]
    c_ids = c_ids[-max_seq_len:]
    r_ids = r_ids[-max_seq_len:]
    d_ts = d_ts[-max_seq_len:]

    with torch.no_grad():
        q_tensor = torch.tensor([q_ids], dtype=torch.long)
        c_tensor = torch.tensor([c_ids], dtype=torch.long)
        r_tensor = torch.tensor([r_ids], dtype=torch.long)
        d_tensor = torch.tensor([d_ts], dtype=torch.float32)
        pred = model(q_tensor, c_tensor, r_tensor, d_tensor)
        score = float(pred[0, -1].item())
        return max(0.0, min(1.0, score))


def _question_concept_key(question: Dict, meta: Dict) -> str:
    qid = _normalize_question_key(question.get("id"))
    q_to_c = meta.get("question_to_primary_concept") or {}
    if qid and qid in q_to_c:
        return str(q_to_c[qid])
    if question.get("source_qid") is not None:
        raw = str(question.get("source_qid"))
        if raw in q_to_c:
            return str(q_to_c[raw])
    return str(question.get("skill_id") or "unknown")


def rank_question_for_student(
    question: Dict,
    records: List[Dict],
    skill_mastery: Optional[Dict[str, float]] = None,
    dkt_next: Optional[float] = None,
) -> Tuple[float, Dict]:
    if skill_mastery is None:
        skill_mastery = estimate_skill_mastery(records)

    if dkt_next is None:
        dkt_next = estimate_dkt_next_correct(records)
    meta = _load_dkt_metadata()
    concept_key = _question_concept_key(question, meta)
    mastery = skill_mastery.get(concept_key)
    if mastery is None:
        mastery = skill_mastery.get(str(question.get("skill_id") or "unknown"), 0.35)

    seen_qids = {str(r.get("problem_id") or r.get("quest_id")) for r in records}
    question_id = str(question.get("id") or "")
    unseen_bonus = 0.18 if question_id not in seen_qids else 0.02

    diff = str(question.get("difficulty") or "").lower()
    diff_boost = {"easy": 0.03, "medium": 0.06, "hard": 0.09}.get(diff, 0.05)

    dkt_need = 0.5 if dkt_next is None else (1.0 - dkt_next)
    remediation = 1.0 - float(mastery)
    score = remediation * 0.68 + unseen_bonus + diff_boost + dkt_need * 0.08

    details = {
        "concept_key": concept_key,
        "mastery": round(float(mastery), 4),
        "dkt_next_correct": None if dkt_next is None else round(float(dkt_next), 4),
        "remediation_need": round(remediation, 4),
        "unseen_bonus": round(unseen_bonus, 4),
        "difficulty_boost": round(diff_boost, 4),
    }
    return score, details
