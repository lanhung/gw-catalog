from __future__ import annotations

import torch
from torch import nn
import torch.nn.functional as F


class Snake(nn.Module):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.alpha = nn.Parameter(torch.ones(1, channels, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + torch.sin(self.alpha * x) ** 2 / (self.alpha + 1e-8)


class ResidualBlock1D(nn.Module):
    def __init__(self, channels: int, kernel_size: int = 7) -> None:
        super().__init__()
        pad = kernel_size // 2
        self.net = nn.Sequential(
            nn.Conv1d(channels, channels, kernel_size, padding=pad, bias=False),
            nn.BatchNorm1d(channels),
            Snake(channels),
            nn.Conv1d(channels, channels, kernel_size, padding=pad, bias=False),
            nn.BatchNorm1d(channels),
        )
        self.act = Snake(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(x + self.net(x))


class MatchEncoder1D(nn.Module):
    """Compact match-style Siamese encoder for GW strain windows."""

    def __init__(self, in_channels: int = 1, d_model: int = 256, emb_dim: int = 128, width_scale: float = 2.0) -> None:
        super().__init__()
        base = max(16, int(32 * width_scale))
        self.features = nn.Sequential(
            nn.Conv1d(in_channels, base, 15, stride=2, padding=7, bias=False),
            nn.BatchNorm1d(base),
            Snake(base),
            nn.MaxPool1d(2),
            nn.Conv1d(base, base * 2, 11, stride=2, padding=5, bias=False),
            nn.BatchNorm1d(base * 2),
            Snake(base * 2),
            ResidualBlock1D(base * 2, 9),
            nn.Conv1d(base * 2, base * 4, 7, stride=2, padding=3, bias=False),
            nn.BatchNorm1d(base * 4),
            Snake(base * 4),
            ResidualBlock1D(base * 4, 7),
            nn.Conv1d(base * 4, base * 4, 5, stride=2, padding=2, bias=False),
            nn.BatchNorm1d(base * 4),
            Snake(base * 4),
        )
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(base * 4, d_model),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, emb_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.head(self.features(x.float()))
        return F.normalize(z, dim=-1)


class NTXentLoss(nn.Module):
    def __init__(self, tau: float = 0.07) -> None:
        super().__init__()
        self.tau = tau

    def forward(self, z1: torch.Tensor, z2: torch.Tensor) -> torch.Tensor:
        z1 = F.normalize(z1.float(), dim=-1)
        z2 = F.normalize(z2.float(), dim=-1)
        n = z1.size(0)
        z = torch.cat([z1, z2], dim=0)
        sim = z @ z.T / self.tau
        sim = sim.masked_fill(torch.eye(2 * n, dtype=torch.bool, device=z.device), -1e9)
        pos = torch.cat([torch.diag(sim, n), torch.diag(sim, -n)], dim=0)
        return -(pos - torch.logsumexp(sim, dim=1)).mean()
