from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

ALLOWED_MORSE_PHASES = (0.0, math.pi / 2, math.pi)
PM_MAX_MASS_MSUN = 1e7


@dataclass(frozen=True)
class LensImage:
    image_index: int
    magnification: float
    time_delay: float
    morse_phase: float


@dataclass(frozen=True)
class LensSystemSample:
    lens_family: str
    lens_mass_msun: float | None
    images: list[LensImage]


def _uniform(rng: np.random.Generator, low: float, high: float) -> float:
    return float(rng.uniform(low, high))


def sample_pm_doublet(rng: np.random.Generator) -> LensSystemSample:
    lens_mass_msun = _uniform(rng, 10.0, PM_MAX_MASS_MSUN)
    mag1 = _uniform(rng, 1.1, 3.0)
    mag2 = _uniform(rng, 0.7, 2.0)
    dt = _uniform(rng, 0.01, 7.5)
    return LensSystemSample(
        lens_family="PM",
        lens_mass_msun=lens_mass_msun,
        images=[
            LensImage(0, mag1, 0.0, 0.0),
            LensImage(1, mag2, dt, math.pi / 2),
        ],
    )


def sample_sis_doublet(rng: np.random.Generator) -> LensSystemSample:
    mag1 = _uniform(rng, 1.2, 4.0)
    mag2 = _uniform(rng, 0.8, 2.5)
    dt = _uniform(rng, 0.1, 15.0)
    return LensSystemSample(
        lens_family="SIS",
        lens_mass_msun=None,
        images=[
            LensImage(0, mag1, 0.0, 0.0),
            LensImage(1, mag2, dt, math.pi / 2),
        ],
    )


def sample_sie_multiplet(rng: np.random.Generator, multiplicity: int) -> LensSystemSample:
    if multiplicity not in (3, 4):
        raise ValueError("multiplicity must be 3 or 4")

    images: list[LensImage] = [LensImage(0, _uniform(rng, 1.2, 3.0), 0.0, 0.0)]
    for idx in range(1, multiplicity):
        images.append(
            LensImage(
                idx,
                _uniform(rng, 0.6, 2.2),
                _uniform(rng, 0.2, 20.0) * idx,
                ALLOWED_MORSE_PHASES[idx % len(ALLOWED_MORSE_PHASES)],
            )
        )
    return LensSystemSample(lens_family="SIE", lens_mass_msun=None, images=images)
