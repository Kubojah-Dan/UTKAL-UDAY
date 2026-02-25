import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score
from torch.utils.data import DataLoader, Dataset

from app.core.bkt_em import em_for_skill

ROOT_DIR = Path(__file__).resolve().parents[2]
XES_DIR = ROOT_DIR / "data" / "XES3G5M"
QUESTION_LEVEL_TRAIN_FILE = XES_DIR / "question_level" / "train_valid_sequences_quelevel.csv"
KC_LEVEL_TRAIN_FILE = XES_DIR / "kc_level" / "train_valid_sequences.csv"
MODELS_DIR = ROOT_DIR / "app" / "models"


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_tokens(raw: str) -> List[str]:
    return [token.strip() for token in str(raw or "").split(",")]


def _parse_primary_concept(token: str) -> str:
    cleaned = str(token or "").strip()
    if not cleaned or cleaned == "-1":
        return "unknown"
    first = cleaned.split("_")[0].strip()
    return first if first and first != "-1" else "unknown"


def _parse_int_token(token: str, invalid: int = -1) -> int:
    token = str(token or "").strip()
    if not token:
        return invalid
    try:
        return int(token)
    except ValueError:
        return invalid


def _load_dkt_sequences(path: Path, max_rows: Optional[int] = None) -> Tuple[List[Dict], Dict[str, str], Dict[str, Dict]]:
    sequences: List[Dict] = []
    q_to_concept_counter: Dict[str, Counter] = defaultdict(Counter)
    unique_questions = set()
    unique_concepts = set()
    fold_counts = Counter()

    with path.open("r", encoding="utf8", newline="") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader):
            if max_rows is not None and row_idx >= max_rows:
                break

            fold = _safe_int(row.get("fold"), -1)
            uid = str(row.get("uid") or f"uid-{row_idx}")
            q_tokens = _parse_tokens(row.get("questions", ""))
            c_tokens = _parse_tokens(row.get("concepts", ""))
            r_tokens = _parse_tokens(row.get("responses", ""))
            t_tokens = _parse_tokens(row.get("timestamps", ""))

            n = min(len(q_tokens), len(c_tokens), len(r_tokens), len(t_tokens))
            if n < 3:
                continue

            q_ids: List[str] = []
            c_ids: List[str] = []
            responses: List[int] = []
            timestamps: List[int] = []

            for i in range(n):
                q_val = _parse_int_token(q_tokens[i], invalid=-1)
                r_val = _parse_int_token(r_tokens[i], invalid=-1)
                ts = _safe_int(t_tokens[i], 0)
                c_key = _parse_primary_concept(c_tokens[i])
                if q_val < 0 or r_val not in (0, 1):
                    continue
                q_key = str(q_val)
                q_ids.append(q_key)
                c_ids.append(c_key)
                responses.append(r_val)
                timestamps.append(ts)

                unique_questions.add(q_key)
                unique_concepts.add(c_key)
                q_to_concept_counter[q_key][c_key] += 1

            if len(q_ids) < 3:
                continue

            sequences.append(
                {
                    "fold": fold,
                    "uid": uid,
                    "q_ids": q_ids,
                    "c_ids": c_ids,
                    "responses": responses,
                    "timestamps": timestamps,
                }
            )
            fold_counts[str(fold)] += 1

    question_to_primary_concept = {}
    for q_key, counter in q_to_concept_counter.items():
        question_to_primary_concept[q_key] = counter.most_common(1)[0][0]

    stats = {
        "sequence_count": len(sequences),
        "unique_questions": len(unique_questions),
        "unique_concepts": len(unique_concepts),
        "fold_counts": dict(fold_counts),
    }
    return sequences, question_to_primary_concept, stats


def _load_bkt_skill_sequences(path: Path, max_rows: Optional[int] = None) -> Tuple[Dict[str, List[List[int]]], Dict[str, int]]:
    per_student_skill = defaultdict(list)
    skill_obs_counts = Counter()

    with path.open("r", encoding="utf8", newline="") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader):
            if max_rows is not None and row_idx >= max_rows:
                break

            uid = str(row.get("uid") or f"uid-{row_idx}")
            concept_tokens = _parse_tokens(row.get("concepts", ""))
            response_tokens = _parse_tokens(row.get("responses", ""))
            n = min(len(concept_tokens), len(response_tokens))
            if n < 2:
                continue

            for i in range(n):
                response = _parse_int_token(response_tokens[i], invalid=-1)
                if response not in (0, 1):
                    continue
                raw_concepts = str(concept_tokens[i] or "").strip()
                if not raw_concepts or raw_concepts == "-1":
                    continue
                for concept in raw_concepts.split("_"):
                    concept = concept.strip()
                    if not concept or concept == "-1":
                        continue
                    key = f"{uid}::{concept}"
                    per_student_skill[key].append(response)
                    skill_obs_counts[concept] += 1

    skill_sequences = defaultdict(list)
    for student_skill, outcomes in per_student_skill.items():
        if len(outcomes) < 2:
            continue
        _, concept = student_skill.split("::", 1)
        skill_sequences[concept].append(outcomes)

    return dict(skill_sequences), dict(skill_obs_counts)


class DKTWindowDataset(Dataset):
    def __init__(
        self,
        sequences: List[Dict],
        question_to_idx: Dict[str, int],
        concept_to_idx: Dict[str, int],
        max_seq_len: int = 200,
        stride: int = 60,
    ):
        self.samples: List[Tuple[List[int], List[int], List[int], List[float], List[float]]] = []
        self.max_seq_len = max(10, int(max_seq_len))
        self.stride = max(10, int(stride))

        for seq in sequences:
            q_raw = seq["q_ids"]
            c_raw = seq["c_ids"]
            r_raw = seq["responses"]
            t_raw = seq["timestamps"]

            q_ids = [question_to_idx.get(q, 0) for q in q_raw]
            c_ids = [concept_to_idx.get(c, 0) for c in c_raw]
            r_ids = [int(v) for v in r_raw]

            deltas = []
            prev_ts = None
            for ts in t_raw:
                if prev_ts is None:
                    delta = 0.0
                else:
                    delta = max(0.0, (_safe_int(ts, 0) - _safe_int(prev_ts, 0)) / 1000.0)
                prev_ts = ts
                deltas.append(min(delta, 3600.0))

            n = len(q_ids)
            if n < 3:
                continue

            for start in range(0, n - 1, self.stride):
                end = min(start + self.max_seq_len, n)
                if end - start < 3:
                    continue
                in_q = q_ids[start : end - 1]
                in_c = c_ids[start : end - 1]
                in_r = r_ids[start : end - 1]
                in_d = deltas[start : end - 1]
                target = [float(v) for v in r_ids[start + 1 : end]]
                self.samples.append((in_q, in_c, in_r, in_d, target))
                if end == n:
                    break

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        q, c, r, d, t = self.samples[index]
        return (
            torch.tensor(q, dtype=torch.long),
            torch.tensor(c, dtype=torch.long),
            torch.tensor(r, dtype=torch.long),
            torch.tensor(d, dtype=torch.float32),
            torch.tensor(t, dtype=torch.float32),
        )


def _collate_batch(batch):
    max_len = max(item[0].shape[0] for item in batch)
    bsz = len(batch)

    q = torch.zeros((bsz, max_len), dtype=torch.long)
    c = torch.zeros((bsz, max_len), dtype=torch.long)
    r = torch.zeros((bsz, max_len), dtype=torch.long)
    d = torch.zeros((bsz, max_len), dtype=torch.float32)
    y = torch.zeros((bsz, max_len), dtype=torch.float32)
    mask = torch.zeros((bsz, max_len), dtype=torch.float32)

    for i, (q_i, c_i, r_i, d_i, y_i) in enumerate(batch):
        n = q_i.shape[0]
        q[i, :n] = q_i
        c[i, :n] = c_i
        r[i, :n] = r_i
        d[i, :n] = d_i
        y[i, :n] = y_i
        mask[i, :n] = 1.0

    return q, c, r, d, y, mask


class DKTModel(nn.Module):
    def __init__(
        self,
        num_questions: int,
        num_concepts: int,
        question_embedding_dim: int = 64,
        concept_embedding_dim: int = 32,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.question_emb = nn.Embedding(num_questions + 1, question_embedding_dim, padding_idx=0)
        self.concept_emb = nn.Embedding(num_concepts + 1, concept_embedding_dim, padding_idx=0)
        self.correct_emb = nn.Embedding(2, 8)
        self.delta_fc = nn.Linear(1, 8)
        self.dropout = nn.Dropout(dropout)

        input_dim = question_embedding_dim + concept_embedding_dim + 8 + 8
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

    def forward(self, q_ids, c_ids, r_ids, delta_times):
        qv = self.question_emb(q_ids)
        cv = self.concept_emb(c_ids)
        rv = self.correct_emb(r_ids)
        dv = torch.tanh(self.delta_fc(delta_times.unsqueeze(-1)))
        x = torch.cat([qv, cv, rv, dv], dim=-1)
        x = self.dropout(x)
        h, _ = self.gru(x)
        logits = self.head(h).squeeze(-1)
        return torch.sigmoid(logits)


def _train_epoch(model, loader, optimizer, device):
    model.train()
    criterion = nn.BCELoss(reduction="none")
    total_loss = 0.0
    total_tokens = 0.0

    for q, c, r, d, y, mask in loader:
        q = q.to(device)
        c = c.to(device)
        r = r.to(device)
        d = d.to(device)
        y = y.to(device)
        mask = mask.to(device)

        optimizer.zero_grad()
        pred = model(q, c, r, d)
        loss_matrix = criterion(pred, y) * mask
        loss = loss_matrix.sum() / mask.sum().clamp_min(1.0)
        loss.backward()
        optimizer.step()

        total_loss += float(loss_matrix.sum().item())
        total_tokens += float(mask.sum().item())

    return total_loss / max(1.0, total_tokens)


def _evaluate(model, loader, device):
    model.eval()
    criterion = nn.BCELoss(reduction="none")
    total_loss = 0.0
    total_tokens = 0.0
    preds = []
    labels = []

    with torch.no_grad():
        for q, c, r, d, y, mask in loader:
            q = q.to(device)
            c = c.to(device)
            r = r.to(device)
            d = d.to(device)
            y = y.to(device)
            mask = mask.to(device)

            pred = model(q, c, r, d)
            loss_matrix = criterion(pred, y) * mask
            total_loss += float(loss_matrix.sum().item())
            total_tokens += float(mask.sum().item())

            active = mask > 0
            preds.extend(pred[active].detach().cpu().tolist())
            labels.extend(y[active].detach().cpu().tolist())

    val_loss = total_loss / max(1.0, total_tokens)
    if len(set(int(v >= 0.5) for v in preds)) < 2 or len(set(int(v) for v in labels)) < 2:
        auc = None
    else:
        auc = float(roc_auc_score(labels, preds))
    if preds:
        accuracy = float(np.mean([(p >= 0.5) == (y >= 0.5) for p, y in zip(preds, labels)]))
    else:
        accuracy = 0.0

    return {"loss": val_loss, "auc": auc, "accuracy": accuracy}


def _train_dkt(
    sequences: List[Dict],
    question_to_primary_concept: Dict[str, str],
    epochs: int,
    batch_size: int,
    lr: float,
    max_seq_len: int,
    stride: int,
    val_fold: int,
    device: str,
):
    question_vocab = sorted({q for seq in sequences for q in seq["q_ids"]})
    concept_vocab = sorted({c for seq in sequences for c in seq["c_ids"]})

    question_to_idx = {q: i + 1 for i, q in enumerate(question_vocab)}
    concept_to_idx = {"unknown": 0}
    for idx, concept in enumerate(concept_vocab, start=1):
        if concept == "unknown":
            continue
        concept_to_idx[concept] = idx

    train_sequences = [s for s in sequences if _safe_int(s.get("fold"), -1) != val_fold]
    val_sequences = [s for s in sequences if _safe_int(s.get("fold"), -1) == val_fold]
    if not val_sequences:
        split = int(len(sequences) * 0.9)
        train_sequences = sequences[:split]
        val_sequences = sequences[split:]

    train_dataset = DKTWindowDataset(
        train_sequences,
        question_to_idx=question_to_idx,
        concept_to_idx=concept_to_idx,
        max_seq_len=max_seq_len,
        stride=stride,
    )
    val_dataset = DKTWindowDataset(
        val_sequences,
        question_to_idx=question_to_idx,
        concept_to_idx=concept_to_idx,
        max_seq_len=max_seq_len,
        stride=stride,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=_collate_batch,
        num_workers=0,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=_collate_batch,
        num_workers=0,
    )

    model = DKTModel(
        num_questions=len(question_to_idx),
        num_concepts=len(concept_to_idx),
        question_embedding_dim=64,
        concept_embedding_dim=32,
        hidden_dim=128,
        num_layers=2,
        dropout=0.2,
    )
    model = model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.6, patience=2
    )

    best_state = None
    best_loss = float("inf")
    history = []
    early_stop_patience = 4
    no_improve = 0

    for epoch in range(1, epochs + 1):
        train_loss = _train_epoch(model, train_loader, optimizer, device)
        val_metrics = _evaluate(model, val_loader, device)
        scheduler.step(val_metrics["loss"])

        row = {
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "val_loss": round(val_metrics["loss"], 6),
            "val_auc": None if val_metrics["auc"] is None else round(val_metrics["auc"], 6),
            "val_accuracy": round(val_metrics["accuracy"], 6),
            "lr": optimizer.param_groups[0]["lr"],
        }
        history.append(row)
        print(
            f"[DKT] Epoch {epoch}/{epochs} "
            f"train_loss={row['train_loss']:.6f} val_loss={row['val_loss']:.6f} "
            f"val_auc={row['val_auc']}"
        )

        if val_metrics["loss"] + 1e-5 < best_loss:
            best_loss = val_metrics["loss"]
            best_state = {k: v.cpu() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= early_stop_patience:
                print("[DKT] Early stopping triggered.")
                break

    if best_state is not None:
        model.load_state_dict(best_state, strict=False)

    final_metrics = _evaluate(model, val_loader, device)
    return {
        "model_state": model.state_dict(),
        "question_to_idx": question_to_idx,
        "concept_to_idx": concept_to_idx,
        "question_to_primary_concept": question_to_primary_concept,
        "history": history,
        "final_metrics": final_metrics,
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "config": {
            "num_questions": len(question_to_idx),
            "num_concepts": len(concept_to_idx),
            "question_embedding_dim": 64,
            "concept_embedding_dim": 32,
            "hidden_dim": 128,
            "num_layers": 2,
            "dropout": 0.2,
            "max_seq_len": max_seq_len,
            "stride": stride,
            "val_fold": val_fold,
        },
    }


def _train_bkt(skill_sequences: Dict[str, List[List[int]]], min_sequences: int) -> Tuple[Dict, Dict]:
    bkt_params = {}
    trained = 0
    skipped = 0
    for skill, sequences in skill_sequences.items():
        if len(sequences) < min_sequences:
            skipped += 1
            continue
        cleaned = [seq for seq in sequences if len(seq) >= 2]
        if len(cleaned) < min_sequences:
            skipped += 1
            continue
        params = em_for_skill(cleaned, max_iter=60, tol=1e-4, verbose=False)
        bkt_params[str(skill)] = params
        trained += 1

    stats = {
        "skills_seen": len(skill_sequences),
        "skills_trained": trained,
        "skills_skipped": skipped,
    }
    return bkt_params, stats


def _ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Train DKT + BKT models on XES3G5M")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=8e-4)
    parser.add_argument("--max-seq-len", type=int, default=200)
    parser.add_argument("--stride", type=int, default=60)
    parser.add_argument("--val-fold", type=int, default=4)
    parser.add_argument("--min-bkt-sequences", type=int, default=20)
    parser.add_argument("--max-train-rows", type=int, default=None)
    parser.add_argument("--max-bkt-rows", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--dkt-out", type=str, default="app/models/dkt_xes3g5m.pt")
    parser.add_argument("--dkt-meta-out", type=str, default="app/models/dkt_xes3g5m_meta.json")
    parser.add_argument("--bkt-out", type=str, default="app/models/bkt_params_xes3g5m.json")
    parser.add_argument("--report-out", type=str, default="app/models/xes_training_report.json")
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    print(f"[Info] Using device: {device}")

    if not QUESTION_LEVEL_TRAIN_FILE.exists():
        raise FileNotFoundError(f"Missing file: {QUESTION_LEVEL_TRAIN_FILE}")
    if not KC_LEVEL_TRAIN_FILE.exists():
        raise FileNotFoundError(f"Missing file: {KC_LEVEL_TRAIN_FILE}")

    print("[Info] Loading question-level sequences for DKT...")
    dkt_sequences, q_to_primary_concept, dkt_data_stats = _load_dkt_sequences(
        QUESTION_LEVEL_TRAIN_FILE, max_rows=args.max_train_rows
    )
    print(
        f"[Info] DKT rows loaded: sequences={dkt_data_stats['sequence_count']} "
        f"questions={dkt_data_stats['unique_questions']} concepts={dkt_data_stats['unique_concepts']}"
    )

    dkt_result = _train_dkt(
        dkt_sequences,
        question_to_primary_concept=q_to_primary_concept,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        max_seq_len=args.max_seq_len,
        stride=args.stride,
        val_fold=args.val_fold,
        device=device,
    )

    print("[Info] Loading KC-level sequences for BKT...")
    skill_sequences, skill_obs_counts = _load_bkt_skill_sequences(
        KC_LEVEL_TRAIN_FILE, max_rows=args.max_bkt_rows
    )
    bkt_params, bkt_stats = _train_bkt(skill_sequences, min_sequences=args.min_bkt_sequences)
    print(
        f"[Info] BKT trained skills: {bkt_stats['skills_trained']} "
        f"(seen={bkt_stats['skills_seen']}, skipped={bkt_stats['skills_skipped']})"
    )

    dkt_out = (ROOT_DIR / args.dkt_out).resolve()
    dkt_meta_out = (ROOT_DIR / args.dkt_meta_out).resolve()
    bkt_out = (ROOT_DIR / args.bkt_out).resolve()
    report_out = (ROOT_DIR / args.report_out).resolve()

    _ensure_parent(dkt_out)
    _ensure_parent(dkt_meta_out)
    _ensure_parent(bkt_out)
    _ensure_parent(report_out)

    torch.save(dkt_result["model_state"], dkt_out)
    dkt_meta = {
        "dataset": "XES3G5M",
        "question_to_idx": dkt_result["question_to_idx"],
        "concept_to_idx": dkt_result["concept_to_idx"],
        "question_to_primary_concept": dkt_result["question_to_primary_concept"],
        "dkt_config": dkt_result["config"],
        "train_samples": dkt_result["train_samples"],
        "val_samples": dkt_result["val_samples"],
        "metrics": dkt_result["final_metrics"],
        "history": dkt_result["history"],
    }
    dkt_meta_out.write_text(json.dumps(dkt_meta, ensure_ascii=False), encoding="utf8")

    bkt_out.write_text(json.dumps(bkt_params, ensure_ascii=False), encoding="utf8")

    report = {
        "dataset": "XES3G5M",
        "seed": args.seed,
        "device": device,
        "dkt": {
            "model_file": str(dkt_out),
            "meta_file": str(dkt_meta_out),
            "metrics": dkt_result["final_metrics"],
            "config": dkt_result["config"],
            "data_stats": dkt_data_stats,
        },
        "bkt": {
            "params_file": str(bkt_out),
            "stats": bkt_stats,
            "min_sequences": args.min_bkt_sequences,
            "skill_observation_counts": skill_obs_counts,
        },
    }
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf8")

    print(f"[Done] DKT model saved to: {dkt_out}")
    print(f"[Done] DKT metadata saved to: {dkt_meta_out}")
    print(f"[Done] BKT parameters saved to: {bkt_out}")
    print(f"[Done] Training report saved to: {report_out}")


if __name__ == "__main__":
    main()
