from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class DetectorNetworkSpec:
    """Configuration for a detector network used during waveform generation."""

    names: tuple[str, ...]
    max_channels: int | None = None

    @classmethod
    def from_string(cls, value: str, max_channels: int | None = None) -> "DetectorNetworkSpec":
        names = tuple(part.strip() for part in value.split(",") if part.strip())
        if not names:
            raise ValueError("detector network must contain at least one detector name")
        return cls(names=names, max_channels=max_channels)


def build_interferometers(bilby_module, spec: DetectorNetworkSpec):
    """Build a bilby InterferometerList and optionally keep only the first N channels."""

    ifos = list(bilby_module.gw.detector.InterferometerList(list(spec.names)))
    if spec.max_channels is not None:
        ifos = ifos[: int(spec.max_channels)]
    if not ifos:
        raise RuntimeError(f"no interferometers returned for detector network {spec.names!r}")
    return ifos


def interferometer_names(ifos: Sequence[object]) -> list[str]:
    return [str(getattr(ifo, "name", f"ifo_{idx}")) for idx, ifo in enumerate(ifos)]


def simulate_detector_network(
    ifos: Sequence[object],
    waveform_generator,
    fd_waveform: dict[str, np.ndarray],
    injection_parameters: dict,
    sampling_frequency: int,
    duration: int,
    n_samples: int,
    peak_reference_offset: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Project one source into an arbitrary detector network.

    Returns arrays with shape ``(n_ifos, n_samples)`` for noisy strain, clean
    signal strain and time arrays, plus per-channel SNR and network SNR.
    """

    data_channels = []
    signal_channels = []
    time_channels = []
    noise_channels = []
    snr_single = []

    for ifo in ifos:
        ifo.set_strain_data_from_power_spectral_density(
            sampling_frequency=sampling_frequency,
            duration=duration,
            start_time=injection_parameters["geocent_time"] - (n_samples - peak_reference_offset) / sampling_frequency,
        )
        noise_f_white = ifo.whitened_frequency_domain_strain
        noise_t_white = np.fft.irfft(noise_f_white, n=n_samples)

        response = ifo.get_detector_response(fd_waveform, injection_parameters)
        snr_squared = np.real(ifo.optimal_snr_squared(response))
        snr_single.append(np.sqrt(np.abs(snr_squared)))

        ifo.inject_signal(waveform_generator=waveform_generator, parameters=injection_parameters, raise_error=False)
        data_f_white = ifo.whitened_frequency_domain_strain
        data_t_white = np.fft.irfft(data_f_white, n=n_samples)
        signal_t_white = data_t_white - noise_t_white

        signal_channels.append(signal_t_white)
        noise_channels.append(noise_t_white)
        time_channels.append(ifo.strain_data.time_array)

    signal_arr = np.stack(signal_channels, axis=0)
    noise_arr = np.stack(noise_channels, axis=0)
    network_envelope = np.sqrt(np.sum(signal_arr * signal_arr, axis=0))
    peak_index = int(np.argmax(np.abs(network_envelope)))
    cut_index = min(peak_index + int(0.05 * sampling_frequency), n_samples)

    signal_trimmed = signal_arr.copy()
    fade_len = n_samples - cut_index
    if fade_len > 0:
        hann_full = np.hanning(2 * fade_len)
        signal_trimmed[:, cut_index:] *= hann_full[fade_len:]

    data_arr = signal_trimmed + noise_arr
    snr_single_arr = np.asarray(snr_single, dtype=np.float64)
    snr_network = float(np.sqrt(np.sum(snr_single_arr * snr_single_arr)))
    return data_arr, signal_trimmed, np.stack(time_channels, axis=0), snr_single_arr, snr_network
