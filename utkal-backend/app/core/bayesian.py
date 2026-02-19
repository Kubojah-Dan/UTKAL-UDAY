import torch
import torch.nn as nn

class DifferentiableBayes(nn.Module):
    def __init__(self, n_skills: int):
        super().__init__()
        self.n = n_skills
        # adjacency logits
        self.A_logits = nn.Parameter(torch.randn(n_skills, n_skills) * 0.01)

    def forward(self):
        A = torch.sigmoid(self.A_logits) * (1 - torch.eye(self.n))
        return A

    def acyclicity_loss(self):
        A = torch.sigmoid(self.A_logits) * (1 - torch.eye(self.n))
        # NOTE: This is placeholder. Use NOTEARS for real DAG enforcement.
        trace = torch.trace(torch.matrix_power(A, 2))
        return trace
