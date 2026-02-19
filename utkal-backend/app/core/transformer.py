import torch
import torch.nn as nn

class TemporalTransformer(nn.Module):
    def __init__(
        self,
        input_dim: int = 8,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 256,
        dropout: float = 0.1
    ):
        super().__init__()

        self.input_fc = nn.Linear(input_dim, d_model)

        # IMPORTANT FIX: batch_first=True
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        self.out = nn.Linear(d_model, 1)

    def forward(self, x):
        """
        x: [batch, seq_len, input_dim]
        returns: [batch, seq_len]
        """
        x = self.input_fc(x)        # [batch, seq_len, d_model]
        x = self.transformer(x)     # [batch, seq_len, d_model]
        logits = self.out(x)        # [batch, seq_len, 1]
        return torch.sigmoid(logits).squeeze(-1)
