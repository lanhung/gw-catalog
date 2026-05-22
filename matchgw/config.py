from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class MatchRunConfig:
    data_root: Path = Path("/root/autodl-tmp/qkzhang")
    model_type: str = "SIS"
    data_mode: str = "noisy"
    out_dir: Path = Path("runs/match_first")
    target_len: int = 8192
    stride: int = 2
    lensed_limit: int | None = 2500
    unlensed_limit: int | None = 2500
    seed: int = 42
    train_frac: float = 0.70
    val_frac: float = 0.15
    batch_size: int = 128
    eval_batch_size: int = 512
    epochs: int = 20
    lr: float = 1e-3
    weight_decay: float = 1e-4
    tau: float = 0.07
    emb_dim: int = 128
    d_model: int = 256
    width_scale: float = 2.0
    aug_roll: int = 128
    aug_scale: float = 0.10
    aug_noise: float = 0.01
    aug_flip: bool = True
    use_hilbert: bool = False
    coarse_topk: int = 10
    coarse_min_score: float | None = 0.85
    coarse_mutual: bool = False
    reciprocal_rank_max: int | None = 3
    row_min_score: float | None = 0.70
    row_min_margin: float | None = 0.0
    edge_rank_bonus: float = 0.0
    tune_for: str = "f1"

    @property
    def family(self) -> str:
        value = self.model_type.upper()
        if value not in {"SIS", "PM"}:
            raise ValueError(f"model_type must be SIS or PM, got {self.model_type!r}")
        return value

    @property
    def mode(self) -> str:
        value = self.data_mode.lower()
        if value not in {"pure", "noisy"}:
            raise ValueError(f"data_mode must be pure or noisy, got {self.data_mode!r}")
        return value

    @property
    def source_dir(self) -> Path:
        return self.data_root / f"{self.family}_data_0222"

    @property
    def strain_tag(self) -> str:
        return "h_strain" if self.mode == "pure" else "data_strain"

    @property
    def l1_path(self) -> Path:
        return self.source_dir / f"{self.family}_{self.strain_tag}_1.npy"

    @property
    def l2_path(self) -> Path:
        return self.source_dir / f"{self.family}_{self.strain_tag}_2.npy"

    @property
    def unlensed_path(self) -> Path:
        name = "unlensed_h_strain.npy" if self.mode == "pure" else "unlensed_data_strain.npy"
        return self.data_root / "Unlensed_data_0222" / name
