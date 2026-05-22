from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .lens_models import (
    ALLOWED_MORSE_PHASES,
    PM_MAX_MASS_MSUN,
    sample_pm_doublet,
    sample_sis_doublet,
    sample_sie_multiplet,
)

_MULTIPLICITY_TO_IMAGES = {"doublet": 2, "triplet": 3, "quadruplet": 4}


@dataclass(frozen=True)
class CatalogConfig:
    n_total: int
    lens_prevalence: float
    multiplicity_distribution: dict[str, float]
    seed: int = 42
    strain_length: int = 4096


def _sample_intrinsic(rng: np.random.Generator) -> dict:
    return {
        "m1": float(rng.uniform(10, 60)),
        "m2": float(rng.uniform(8, 45)),
        "chi1": float(rng.uniform(-0.99, 0.99)),
        "chi2": float(rng.uniform(-0.99, 0.99)),
        "z": float(rng.uniform(0.05, 2.5)),
        "ra": float(rng.uniform(0, 2 * np.pi)),
        "dec": float(rng.uniform(-np.pi / 2, np.pi / 2)),
        "iota": float(rng.uniform(0, np.pi)),
        "psi": float(rng.uniform(0, np.pi)),
        "phi_c": float(rng.uniform(0, 2 * np.pi)),
    }


def _base_strain(rng: np.random.Generator, length: int) -> np.ndarray:
    x = np.linspace(0.0, 1.0, length, dtype=np.float32)
    f = float(rng.uniform(20, 120))
    phase = float(rng.uniform(0, 2 * np.pi))
    env = np.exp(-6 * x).astype(np.float32, copy=False)
    wave = (np.sin(2 * np.pi * f * x + phase) * env).astype(np.float32, copy=False)
    noise = rng.normal(0.0, 0.03, size=length).astype(np.float32)
    out = wave + noise
    out /= np.float32(float(np.std(out, dtype=np.float64)) + 1e-8)
    return out.astype(np.float32, copy=False)


def _lensed_strain(base: np.ndarray, magnification: float, shift: int) -> np.ndarray:
    return (np.roll(base, shift) * np.sqrt(magnification)).astype(np.float32)


def _validate_inputs(cfg: CatalogConfig) -> None:
    if cfg.n_total <= 0:
        raise ValueError("n_total must be > 0")
    if cfg.strain_length <= 0:
        raise ValueError("strain_length must be > 0")
    if not (0 <= cfg.lens_prevalence <= 1):
        raise ValueError("lens_prevalence must be in [0, 1]")
    if not cfg.multiplicity_distribution:
        raise ValueError("multiplicity_distribution must not be empty")

    unknown = set(cfg.multiplicity_distribution) - set(_MULTIPLICITY_TO_IMAGES)
    if unknown:
        raise ValueError(f"unsupported multiplicity labels: {sorted(unknown)}")

    probs = np.array(list(cfg.multiplicity_distribution.values()), dtype=np.float64)
    if np.any(probs < 0):
        raise ValueError("multiplicity_distribution probabilities must be non-negative")
    if not np.isclose(float(probs.sum()), 1.0):
        raise ValueError("multiplicity_distribution probabilities must sum to 1")


def _stable_id(prefix: str, idx: int) -> str:
    return f"{prefix}-{idx:08d}"


def _sample_multiplicity(
    rng: np.random.Generator,
    distribution: dict[str, float],
    max_images: int,
) -> str | None:
    choices = []
    for label in distribution:
        n_images = _MULTIPLICITY_TO_IMAGES[label]
        remainder = max_images - n_images
        if distribution[label] > 0 and n_images <= max_images and remainder != 1:
            choices.append(label)
    if not choices:
        return None

    probs = np.array([distribution[label] for label in choices], dtype=np.float64)
    probs = probs / probs.sum()
    return str(rng.choice(choices, p=probs))


def _sample_lens_system(rng: np.random.Generator, multiplicity: str):
    if multiplicity == "doublet":
        return sample_sis_doublet(rng) if rng.random() > 0.5 else sample_pm_doublet(rng)
    if multiplicity == "triplet":
        return sample_sie_multiplet(rng, 3)
    if multiplicity == "quadruplet":
        return sample_sie_multiplet(rng, 4)
    raise ValueError(f"unsupported multiplicity label: {multiplicity}")


def generate_catalog(cfg: CatalogConfig) -> list[dict]:
    _validate_inputs(cfg)
    rng = np.random.default_rng(cfg.seed)
    events: list[dict] = []
    target_lensed_events = int(cfg.n_total * cfg.lens_prevalence)
    source_idx = 0
    event_idx = 0
    lensed_count = 0

    while target_lensed_events - lensed_count >= 2:
        remaining_lensed = target_lensed_events - lensed_count
        mult = _sample_multiplicity(rng, cfg.multiplicity_distribution, remaining_lensed)
        if mult is None:
            break

        source_id = _stable_id("SRC", source_idx)
        source_idx += 1
        intrinsic = _sample_intrinsic(rng)
        base = _base_strain(rng, cfg.strain_length)
        system = _sample_lens_system(rng, mult)

        if system.lens_family == "PM" and system.lens_mass_msun is not None:
            assert system.lens_mass_msun <= PM_MAX_MASS_MSUN

        for img in system.images:
            assert img.morse_phase in ALLOWED_MORSE_PHASES
            shift = int(min(max(cfg.strain_length - 1, 0), img.time_delay * 8))
            strain = _lensed_strain(base, img.magnification, shift)
            events.append(
                {
                    "event_id": _stable_id("EVT", event_idx),
                    "source_id": source_id,
                    "system_type": mult,
                    "image_index": img.image_index,
                    "magnification": float(img.magnification),
                    "time_delay": float(img.time_delay),
                    "morse_phase": float(img.morse_phase),
                    "lens_family": system.lens_family,
                    "lens_mass_msun": system.lens_mass_msun,
                    "intrinsic_params": intrinsic,
                    "strain": strain,
                }
            )
            event_idx += 1
            lensed_count += 1

    n_isolated = cfg.n_total - len(events)
    for _ in range(n_isolated):
        intrinsic = _sample_intrinsic(rng)
        strain = _base_strain(rng, cfg.strain_length)
        source_id = _stable_id("SRC", source_idx)
        source_idx += 1
        events.append(
            {
                "event_id": _stable_id("EVT", event_idx),
                "source_id": source_id,
                "system_type": "isolated",
                "image_index": 0,
                "magnification": 1.0,
                "time_delay": 0.0,
                "morse_phase": 0.0,
                "lens_family": "none",
                "lens_mass_msun": None,
                "intrinsic_params": intrinsic,
                "strain": strain,
            }
        )
        event_idx += 1

    order = rng.permutation(len(events))
    return [events[int(i)] for i in order]
