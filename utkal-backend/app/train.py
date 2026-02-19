import argparse
import os
import pickle
import random
from typing import List, Dict, Any
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# ---------- Simple LSTM model ----------
class SeqLSTM(nn.Module):
    def __init__(self, input_dim=4, hidden_dim=64, num_layers=2, dropout=0.1):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

    def forward(self, x, lengths=None):
        # x: [B, T, D]
        packed_out, _ = self.lstm(x)  # [B, T, H]
        # take last time-step features
        out = packed_out[:, -1, :]  # [B, H]
        return self.fc(out)  # [B, 1]

# ---------- Dataset ----------
class SequenceDataset(Dataset):
    def __init__(self, sequences: List[Dict[str, Any]], max_seq=50):
        self.max_seq = max_seq
        self.samples = []
        for seq in sequences:
            steps = seq.get("steps", []) if isinstance(seq, dict) else seq
            if len(steps) < 2:
                continue
            # sliding windows: use previous up to max_seq to predict current correct
            for i in range(1, len(steps)):
                prev = steps[max(0, i - max_seq):i]
                y = float(steps[i].get("correct", 0.0))
                # build features per step: [correct_prev, timeTaken_scaled, hintCount_scaled, skill_id_norm]
                fv = []
                for s in prev:
                    correct_prev = float(s.get("correct", 0.0))
                    timeTaken = float(s.get("timeTaken", 0.0)) / 1000.0  # sec scaled
                    hintCount = float(s.get("hintCount", 0.0))
                    skill_id = float(s.get("skill_id", 0)) / 100.0
                    fv.append([correct_prev, timeTaken, hintCount, skill_id])
                # pad to max_seq from left
                if len(fv) < max_seq:
                    pad_len = max_seq - len(fv)
                    fv = [[0.0]*4]*pad_len + fv
                else:
                    fv = fv[-max_seq:]
                self.samples.append((fv, y))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        x, y = self.samples[idx]
        return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

# ---------- training util ----------
def collate_fn(batch):
    xs = torch.stack([b[0] for b in batch], dim=0)
    ys = torch.stack([b[1] for b in batch], dim=0)
    return xs, ys

def load_sequences(pkl_path):
    with open(pkl_path, "rb") as f:
        obj = pickle.load(f)
    # flexible formats
    if isinstance(obj, dict) and "sequences" in obj:
        seqs = obj["sequences"]
    elif isinstance(obj, list):
        seqs = obj
    else:
        # try to find 'sequences' in nested dicts
        seqs = obj.get("sequences") if isinstance(obj, dict) else []
        if seqs is None:
            raise ValueError("Unsupported pickle format for sequences.pkl")
    return seqs

def train(pkl_path, epochs=5, batch_size=128, lr=1e-3, out="app/models/temporal_lstm.pt"):
    print("Loading:", pkl_path)
    sequences = load_sequences(pkl_path)
    random.shuffle(sequences)
    split = int(len(sequences)*0.9)
    train_seqs = sequences[:split]
    val_seqs = sequences[split:]

    train_ds = SequenceDataset(train_seqs)
    val_ds = SequenceDataset(val_seqs)

    print(f"Train samples: {len(train_ds)} Val samples: {len(val_ds)}")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SeqLSTM(input_dim=4, hidden_dim=128)
    model.to(device)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device).unsqueeze(1)
            optimizer.zero_grad()
            out = model(xb)
            loss = criterion(out, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_train = total_loss / max(1, len(train_loader))
        # val
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device)
                yb = yb.to(device).unsqueeze(1)
                out = model(xb)
                loss = criterion(out, yb)
                val_loss += loss.item()
        avg_val = val_loss / max(1, len(val_loader))
        print(f"Epoch {epoch+1}/{epochs} - train_loss: {avg_train:.4f} val_loss: {avg_val:.4f}")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    torch.save(model.state_dict(), out)
    print("Saved model to", out)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pkl", help="processed sequences pickle, e.g. data/processed/sequences.pkl")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--out", default="app/models/temporal_lstm.pt")
    args = parser.parse_args()
    train(args.pkl, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, out=args.out)
