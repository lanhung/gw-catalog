from __future__ import annotations

import numpy as np


def rescale_unit(x: float) -> float:
    return float(max(0.0, min(1.0, (x + 1.0) / 2.0)))


def embed_only_scores(candidate_edges: dict[tuple[int, int], float]) -> dict[tuple[int, int], float]:
    return {edge: rescale_unit(score) for edge, score in candidate_edges.items()}


def lensgraph_scores(candidate_edges: dict[tuple[int, int], float], embeddings: np.ndarray) -> dict[tuple[int, int], float]:
    """Symmetric lightweight reranker over retrieved hard candidates.

    The score combines cosine similarity with a local rank-like confidence
    term. It is deterministic and cheap, intended to make the MVP pipeline
    runnable before the trainable PI-ResNet reranker is wired in.
    """
    if not candidate_edges:
        return {}
    vals = np.array(list(candidate_edges.values()), dtype=np.float32)
    med = float(np.median(vals))
    spread = float(np.percentile(vals, 90) - np.percentile(vals, 10) + 1e-6)
    out: dict[tuple[int, int], float] = {}
    for edge, cos in candidate_edges.items():
        calibrated = 1.0 / (1.0 + np.exp(-(float(cos) - med) * 8.0 / spread))
        out[edge] = float(calibrated)
    return out
