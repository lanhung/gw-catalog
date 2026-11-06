"""Generate whitened strain pairs for the ler-based realistic population.

Drop-in replacement for the original ``generate_sis_catalog.py`` data
generator.  It keeps the original storage layout (whitened detector data,
whitened signal, time array, per-detector and network optimal SNR; peak
aligned at sample N - 1500 with a Hann fade after the peak) but takes the
sources, lenses, image magnifications, time delays and image types from the
realistic ``ler`` population written by ``ler_realistic_population.py``.

Differences from the original generator, all deliberate:

* source-frame masses, redshifts, spins and sky positions follow the LVK-like
  population; lenses are EPL + shear galaxies; the two brightest *detected*
  images of each system form the pair (quads contribute their two brightest);
* the Morse phase follows the image type from the lens solver
  (type I: n = 0, type II: n = 1/2, type III: n = 1);
* as in the original, the second image is injected at geocent_time + time
  delay, so the Earth has rotated between the two arrivals; the redundant
  exp(-2 pi i f t_d) factor that the original also applied inside the
  amplification function (a circular shift of the 24 s segment, undone by the
  peak alignment) is dropped;
* magnification enters once, through the amplification factor sqrt(|mu|);
* detector sets: O4 (H1, L1 with the aLIGO O4 ASD; V1 with the AdV ASD) or
  ET (bilby's triangular Einstein Telescope, ET-D).

Outputs (``--out`` directory, prefix ``<config>_``):
  lensed_data_strain_1.npy, lensed_data_strain_2.npy   (n, n_ifos, N) float32 whitened data
  lensed_h_strain_1.npy,    lensed_h_strain_2.npy      whitened signal only
  lensed_time_array_1.npy,  lensed_time_array_2.npy    (n, N) float64 GPS times
  lensed_snr_single_{1,2}.npy, lensed_snr_network_{1,2}.npy
  lensed_meta.csv            one row per pair with all source/lens/image parameters
  unlensed_data_strain.npy, unlensed_h_strain.npy, unlensed_time_array.npy,
  unlensed_snr_single.npy, unlensed_snr_network.npy, unlensed_meta.csv

Run inside the ler virtual environment (bilby + lalsuite are installed there):

  /home/user/ler-venv/bin/python scripts/population/generate_strain_from_ler.py \
      --config O4 --ler-dir /tmp/claude-0/lertest/ler_data_O4 --out data/ler_strain_O4 --n-max 50

Use ``--n-max`` for a validation run; drop it on the server for the full set.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MORSE = {1: 0.0, 2: 0.5, 3: 1.0}
PEAK_OFFSET_SAMPLES = 1500  # original generator: peak placed at N - 1500
FADE_AFTER_PEAK_S = 0.05


def load_ler_json(path: Path) -> dict:
    d = json.loads(path.read_text())
    return {k: np.asarray(v) for k, v in d.items()}


def detectors(config: str):
    import bilby

    if config == "O4":
        ifos = bilby.gw.detector.InterferometerList(["H1", "L1", "V1"])
        for ifo in ifos:
            asd = "aLIGO_O4_high_asd.txt" if ifo.name in ("H1", "L1") else "AdV_asd.txt"
            ifo.power_spectral_density = bilby.gw.detector.PowerSpectralDensity(asd_file=asd)
        return ifos
    if config == "ET":
        ifos = bilby.gw.detector.InterferometerList(["ET"])
        for ifo in ifos:
            ifo.power_spectral_density = bilby.gw.detector.PowerSpectralDensity(psd_file="ET_D_psd.txt")
        return ifos
    raise ValueError(config)


def lensed_fd_model(frequency_array, mass_1, mass_2, a_1, a_2, tilt_1, tilt_2, phi_12, phi_jl,
                    luminosity_distance, theta_jn, psi, phase, geocent_time, ra, dec,
                    magnification, morse_index, **kwargs):
    """Unlensed BBH waveform times the geometric-optics amplification factor of one image."""
    import bilby

    h = bilby.gw.source.lal_binary_black_hole(
        frequency_array, mass_1=mass_1, mass_2=mass_2, a_1=a_1, a_2=a_2, tilt_1=tilt_1, tilt_2=tilt_2,
        phi_12=phi_12, phi_jl=phi_jl, luminosity_distance=luminosity_distance, theta_jn=theta_jn,
        psi=psi, phase=phase, geocent_time=geocent_time, ra=ra, dec=dec, **kwargs)
    if h is None:
        return None
    F = np.sqrt(abs(magnification)) * np.exp(-1j * np.pi * morse_index * np.sign(frequency_array))
    return {"plus": h["plus"] * F, "cross": h["cross"] * F}


def pair_rows(lp: dict, snr_th: float, n_max: int | None) -> list[dict]:
    """Choose the two brightest detected images of each system and flatten the parameters."""
    mu = lp["magnifications"].astype(float)
    dt = lp["time_delays"].astype(float)
    itype = lp["image_type"].astype(float)
    snr = lp["optimal_snr_net"].astype(float)
    rows = []
    for i in range(mu.shape[0]):
        det = np.where(np.nan_to_num(snr[i]) >= snr_th)[0]
        if len(det) < 2:
            continue
        order = det[np.argsort(-np.abs(mu[i, det]))]
        a, b = order[0], order[1]
        if dt[i, b] < dt[i, a]:  # keep arrival order: image 1 arrives first
            a, b = b, a
        zs = float(lp["zs"][i])
        row = {
            "system_index": i, "zs": zs, "zl": float(lp["zl"][i]), "sigma": float(lp["sigma"][i]),
            "q": float(lp["q"][i]), "gamma": float(lp["gamma"][i]),
            "gamma1": float(lp["gamma1"][i]), "gamma2": float(lp["gamma2"][i]),
            "theta_E_rad": float(lp["theta_E"][i]) if "theta_E" in lp else np.nan,
            "n_images": int(lp["n_images"][i]),
            "mass_1_source": float(lp["mass_1_source"][i]), "mass_2_source": float(lp["mass_2_source"][i]),
            "mass_1": float(lp["mass_1_source"][i]) * (1 + zs), "mass_2": float(lp["mass_2_source"][i]) * (1 + zs),
            "luminosity_distance": float(lp["luminosity_distance"][i]),
            "a_1": float(lp["a_1"][i]) if "a_1" in lp else 0.0, "a_2": float(lp["a_2"][i]) if "a_2" in lp else 0.0,
            "tilt_1": float(lp["tilt_1"][i]) if "tilt_1" in lp else 0.0, "tilt_2": float(lp["tilt_2"][i]) if "tilt_2" in lp else 0.0,
            "phi_12": float(lp["phi_12"][i]) if "phi_12" in lp else 0.0, "phi_jl": float(lp["phi_jl"][i]) if "phi_jl" in lp else 0.0,
            "theta_jn": float(lp["theta_jn"][i]), "psi": float(lp["psi"][i]), "phase": float(lp["phase"][i]),
            "geocent_time": float(lp["geocent_time"][i]), "ra": float(lp["ra"][i]), "dec": float(lp["dec"][i]),
            "mu_1": float(mu[i, a]), "mu_2": float(mu[i, b]),
            "type_1": int(itype[i, a]), "type_2": int(itype[i, b]),
            "morse_1": MORSE[int(itype[i, a])], "morse_2": MORSE[int(itype[i, b])],
            "delay_s": float(dt[i, b] - dt[i, a]),
            "snr_ler_1": float(snr[i, a]), "snr_ler_2": float(snr[i, b]),
        }
        rows.append(row)
        if n_max and len(rows) >= n_max:
            break
    return rows


def inject_one(ifos, wfg, params: dict, N: int, fs: float, rng_seed: int):
    """Inject one signal into fresh Gaussian noise; return whitened data, whitened signal, times, SNRs."""
    import bilby

    bilby.core.utils.random.seed(rng_seed)
    fd = wfg.frequency_domain_strain(params)
    target = N - PEAK_OFFSET_SAMPLES
    data = np.empty((len(ifos), N), dtype=np.float32)
    sig = np.empty((len(ifos), N), dtype=np.float32)
    times = np.empty(N, dtype=np.float64)
    snr_single = np.empty(len(ifos))
    snr2 = 0.0
    for j, ifo in enumerate(ifos):
        ifo.set_strain_data_from_power_spectral_density(
            sampling_frequency=fs, duration=N / fs,
            start_time=params["geocent_time"] - (N / fs - PEAK_OFFSET_SAMPLES / fs))
        n_t_white = np.fft.irfft(ifo.whitened_frequency_domain_strain, n=N)
        response = ifo.get_detector_response(fd, params)
        s2 = float(np.real(ifo.optimal_snr_squared(response)))
        snr_single[j] = np.sqrt(abs(s2))
        snr2 += abs(s2)
        ifo.inject_signal(waveform_generator=wfg, parameters=params)
        d_t_white = np.fft.irfft(ifo.whitened_frequency_domain_strain, n=N)
        h_white = d_t_white - n_t_white
        shift = target - int(np.argmax(np.abs(h_white)))
        h_white = np.roll(h_white, shift)
        index = min(target + int(FADE_AFTER_PEAK_S * fs), N)
        fade = N - index
        if fade > 0:
            h_white[index:] *= np.hanning(2 * fade)[fade:]
        data[j] = h_white + n_t_white
        sig[j] = h_white
        if j == 0:
            times[:] = ifo.strain_data.time_array
    return data, sig, times, snr_single, np.sqrt(snr2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", choices=["O4", "ET"], required=True)
    ap.add_argument("--ler-dir", required=True, help="ler_data_<config> directory written by ler_realistic_population.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-max", type=int, default=None)
    ap.add_argument("--snr-th", type=float, default=8.0)
    ap.add_argument("--duration", type=float, default=24.0)
    ap.add_argument("--fs", type=float, default=4096.0)
    ap.add_argument("--fmin", type=float, default=20.0)
    ap.add_argument("--approximant", default="IMRPhenomXPHM")
    ap.add_argument("--seed", type=int, default=20261106)
    args = ap.parse_args()

    import bilby

    bilby.core.utils.logger.setLevel("WARNING")
    out = REPO / args.out
    out.mkdir(parents=True, exist_ok=True)
    N = int(args.duration * args.fs)
    ifos = detectors(args.config)
    n_ifos = len(ifos)
    wf_args = dict(waveform_approximant=args.approximant, reference_frequency=10.0, minimum_frequency=args.fmin)
    wfg_lensed = bilby.gw.waveform_generator.WaveformGenerator(
        sampling_frequency=args.fs, duration=args.duration, frequency_domain_source_model=lensed_fd_model,
        waveform_arguments=wf_args)
    wfg_plain = bilby.gw.waveform_generator.WaveformGenerator(
        sampling_frequency=args.fs, duration=args.duration,
        frequency_domain_source_model=bilby.gw.source.lal_binary_black_hole, waveform_arguments=wf_args)

    ler_dir = Path(args.ler_dir)
    lp = load_ler_json(ler_dir / f"n_lensed_detectable_{args.config}.json")
    rows = pair_rows(lp, args.snr_th, args.n_max)
    n = len(rows)
    print(f"[{args.config}] generating {n} lensed pairs, {n_ifos} detectors, N={N}", flush=True)
    pre = f"{args.config}_lensed"
    mm = {}
    for k in (1, 2):
        mm[f"data_{k}"] = np.lib.format.open_memmap(out / f"{pre}_data_strain_{k}.npy", mode="w+", dtype=np.float32, shape=(n, n_ifos, N))
        mm[f"h_{k}"] = np.lib.format.open_memmap(out / f"{pre}_h_strain_{k}.npy", mode="w+", dtype=np.float32, shape=(n, n_ifos, N))
        mm[f"t_{k}"] = np.lib.format.open_memmap(out / f"{pre}_time_array_{k}.npy", mode="w+", dtype=np.float64, shape=(n, N))
        mm[f"snr_single_{k}"] = np.lib.format.open_memmap(out / f"{pre}_snr_single_{k}.npy", mode="w+", dtype=np.float64, shape=(n, n_ifos))
        mm[f"snr_net_{k}"] = np.lib.format.open_memmap(out / f"{pre}_snr_network_{k}.npy", mode="w+", dtype=np.float64, shape=(n,))
    t0 = time.time()
    for i, row in enumerate(rows):
        base = {k: row[k] for k in ("mass_1", "mass_2", "a_1", "a_2", "tilt_1", "tilt_2", "phi_12", "phi_jl",
                                    "luminosity_distance", "theta_jn", "psi", "phase", "ra", "dec")}
        for k in (1, 2):
            params = dict(base, geocent_time=row["geocent_time"] + (row["delay_s"] if k == 2 else 0.0),
                          magnification=row[f"mu_{k}"], morse_index=row[f"morse_{k}"])
            d, s, t, ss, sn = inject_one(ifos, wfg_lensed, params, N, args.fs, args.seed + 10 * i + k)
            mm[f"data_{k}"][i], mm[f"h_{k}"][i], mm[f"t_{k}"][i] = d, s, t
            mm[f"snr_single_{k}"][i], mm[f"snr_net_{k}"][i] = ss, sn
            row[f"snr_bilby_{k}"] = sn
        if (i + 1) % 20 == 0 or i + 1 == n:
            print(f"  lensed {i + 1}/{n}  {(time.time() - t0) / (i + 1):.2f} s per pair", flush=True)
    for v in mm.values():
        v.flush()
    pd.DataFrame(rows).to_csv(out / f"{pre}_meta.csv", index=False)

    up_path = ler_dir / f"n_unlensed_detectable_{args.config}.json"
    if up_path.exists():
        up = load_ler_json(up_path)
        n_u = len(up["zs"]) if args.n_max is None else min(args.n_max, len(up["zs"]))
        print(f"[{args.config}] generating {n_u} unlensed events", flush=True)
        preu = f"{args.config}_unlensed"
        ud = np.lib.format.open_memmap(out / f"{preu}_data_strain.npy", mode="w+", dtype=np.float32, shape=(n_u, n_ifos, N))
        uh = np.lib.format.open_memmap(out / f"{preu}_h_strain.npy", mode="w+", dtype=np.float32, shape=(n_u, n_ifos, N))
        ut = np.lib.format.open_memmap(out / f"{preu}_time_array.npy", mode="w+", dtype=np.float64, shape=(n_u, N))
        uss = np.lib.format.open_memmap(out / f"{preu}_snr_single.npy", mode="w+", dtype=np.float64, shape=(n_u, n_ifos))
        usn = np.lib.format.open_memmap(out / f"{preu}_snr_network.npy", mode="w+", dtype=np.float64, shape=(n_u,))
        urows = []
        for i in range(n_u):
            zs = float(up["zs"][i])
            params = {
                "mass_1": float(up["mass_1_source"][i]) * (1 + zs), "mass_2": float(up["mass_2_source"][i]) * (1 + zs),
                "a_1": float(up["a_1"][i]) if "a_1" in up else 0.0, "a_2": float(up["a_2"][i]) if "a_2" in up else 0.0,
                "tilt_1": float(up["tilt_1"][i]) if "tilt_1" in up else 0.0, "tilt_2": float(up["tilt_2"][i]) if "tilt_2" in up else 0.0,
                "phi_12": float(up["phi_12"][i]) if "phi_12" in up else 0.0, "phi_jl": float(up["phi_jl"][i]) if "phi_jl" in up else 0.0,
                "luminosity_distance": float(up["luminosity_distance"][i]), "theta_jn": float(up["theta_jn"][i]),
                "psi": float(up["psi"][i]), "phase": float(up["phase"][i]), "geocent_time": float(up["geocent_time"][i]),
                "ra": float(up["ra"][i]), "dec": float(up["dec"][i]),
            }
            d, s, t, ss, sn = inject_one(ifos, wfg_plain, params, N, args.fs, args.seed + 1_000_000 + i)
            ud[i], uh[i], ut[i], uss[i], usn[i] = d, s, t, ss, sn
            urows.append(dict(params, zs=zs, mass_1_source=float(up["mass_1_source"][i]), mass_2_source=float(up["mass_2_source"][i]),
                              snr_ler=float(up["optimal_snr_net"][i]) if "optimal_snr_net" in up else np.nan, snr_bilby=sn))
            if (i + 1) % 20 == 0 or i + 1 == n_u:
                print(f"  unlensed {i + 1}/{n_u}", flush=True)
        for v in (ud, uh, ut, uss, usn):
            v.flush()
        pd.DataFrame(urows).to_csv(out / f"{preu}_meta.csv", index=False)

    (out / f"{args.config}_generation_meta.json").write_text(json.dumps({
        "config": args.config, "detectors": [ifo.name for ifo in ifos], "duration_s": args.duration, "fs_hz": args.fs,
        "fmin_hz": args.fmin, "approximant": args.approximant, "N": N, "peak_index": N - PEAK_OFFSET_SAMPLES,
        "n_lensed_pairs": n, "snr_threshold": args.snr_th, "seed": args.seed, "wall_s": time.time() - t0}, indent=2))
    print("done", flush=True)


if __name__ == "__main__":
    main()
