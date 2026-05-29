#!/usr/bin/env python3
# Auto-generated from unlensed GW events.ipynb
# Detector branch: LIGO

# %% Cell 0
# 必要package
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import bilby
from bilby.gw.conversion import luminosity_distance_to_redshift
from bilby.gw.conversion import redshift_to_luminosity_distance
from astropy import units
from astropy import constants as const
from astropy.cosmology import Planck18 as cosmo
from lenstronomy.LensModel.lens_model import LensModel
from lenstronomy.Cosmo.lens_cosmo import LensCosmo
from lenstronomy.LensModel.Solver.lens_equation_solver import LensEquationSolver
from gwpy.time import Time as GWTime
import os
import tempfile
import shutil

# 在系统临时文件夹中创建临时文件
tmp_dir = tempfile.gettempdir()

# 宇宙学模型
bilby.gw.cosmology.DEFAULT_COSMOLOGY=cosmo
bilby.gw.cosmology.COSMOLOGY = [cosmo, cosmo.name]
bilby.gw.cosmology.get_cosmology()  # 查看默认宇宙学模型

# Output path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUTPUT_ROOT = os.environ.get("GW_OUTPUT_ROOT", os.path.join(SCRIPT_DIR, "outputs"))
RUN_NAME = os.environ.get("GW_RUN_NAME", "unlensed_GW_events_LIGO")
output_dir = os.path.join(OUTPUT_ROOT, RUN_NAME)
os.makedirs(output_dir, exist_ok=True)

# Keep all relative CSV/NPY outputs for this run under one directory.
os.chdir(output_dir)
tmp_dir = os.path.join(output_dir, "tmp")
os.makedirs(tmp_dir, exist_ok=True)
print(f"Writing outputs to: {output_dir}")

# %% Cell 2
# random seed
n=6130000
# n=613

# %% Cell 4
# 总样本个数
n_samples=10000

# 源红移范围
z_min=0.01
z_max=2
d_L_min = redshift_to_luminosity_distance(z_min)
d_L_max = redshift_to_luminosity_distance(z_max)
print("d_L_min:",d_L_min)
print("d_L_max:",d_L_max)


# 源质量范围
m_min=10
m_max=70

# 波形到达地心时间范围，可自定义时间段
time_start = GWTime('2015-09-14 09:50:45.39', scale='utc').gps
time_end=GWTime('2025-12-10 17:18:45.39', scale='utc').gps

time_end

# %% Cell 6
sampling_frequency=4096  # f_s >= 2*f_max   #
duration=24  # len(strain_data) = f_s*duration
minimum_frequency=20.0

# %% Cell 8
bilby.core.utils.random.seed(n)


# sampling from priors
def prior_GW():
    priors = bilby.core.prior.PriorDict()
    priors['luminosity_distance']=bilby.gw.prior.UniformComovingVolume(
        name="luminosity_distance", minimum=d_L_min, maximum=d_L_max, latex_label="r'$d_L$ (Mpc)'")
    priors['mass_1_source']= bilby.core.prior.Uniform(m_min, m_max, 'mass_1_source')
    priors['mass_2_source']= bilby.core.prior.Uniform(m_min, m_max, 'mass_2_source')
    priors['a_1']= bilby.core.prior.Uniform(0, 0.99, 'a_1')
    priors['a_2']= bilby.core.prior.Uniform(0, 0.99, 'a_2')
    priors['tilt_1']= bilby.core.prior.Sine(name='tilt_1')
    priors['tilt_2']= bilby.core.prior.Sine(name='tilt_2')
    priors['phi_12']= bilby.core.prior.Uniform(0, 2 * np.pi, 'phi_12', boundary='periodic')
    priors['phi_jl']= bilby.core.prior.Uniform(0, 2 * np.pi, 'phi_jl', boundary='periodic')
    priors['ra']= bilby.core.prior.Uniform(0, 2 * np.pi, 'ra', boundary='periodic')
    priors['dec']= bilby.core.prior.Cosine(name='dec')
    priors['theta_jn']= bilby.core.prior.Sine(name='theta_jn')
    priors['psi']= bilby.core.prior.Uniform(0, np.pi, 'psi', boundary='periodic')
    priors['phase']= bilby.core.prior.Uniform(0, 2 * np.pi, 'phase', boundary='periodic')
    priors['geocent_time']= bilby.core.prior.Uniform(time_start, time_end, 'geocent_time')

    return priors

priors = prior_GW()
samples = priors.sample(n_samples)
print(samples.keys())

fig, axes = plt.subplots(5, 4, figsize=(20, 15))
axes = axes.flatten()
for i, key in enumerate(samples.keys()):
    ax = axes[i]
    ax.hist(samples[key], bins=50, density=True, label=key)
    ax.set_xlabel(key)
    ax.set_ylabel('Density')
    ax.legend()
for j in range(i+1, len(axes)):
    fig.delaxes(axes[j])
plt.tight_layout()
# plt.savefig('source_samples.pdf')


# 保存数据
source_params = pd.DataFrame(samples)
source_params.to_csv('source_samples.csv', index=False)
source_params

# %% Cell 11
bilby.core.utils.random.seed(n + 1)

N = int(sampling_frequency * duration)

waveform_arguments = dict(
    waveform_approximant='IMRPhenomXPHM',
    reference_frequency=10.,
    minimum_frequency=minimum_frequency
)

waveform_generator = bilby.gw.WaveformGenerator(
    duration=duration,
    sampling_frequency=sampling_frequency,
    frequency_domain_source_model=bilby.gw.source.lal_binary_black_hole,
    parameter_conversion=bilby.gw.conversion.convert_to_lal_binary_black_hole_parameters,
    waveform_arguments=waveform_arguments
)

source_params = pd.read_csv('source_samples.csv')
n_events = len(source_params)


ifos = bilby.gw.detector.InterferometerList(["H1", "L1"])
ifo_names = [ifo.name for ifo in ifos]
n_ifos = len(ifos)



# 输出文件
tmp_data = os.path.join(tmp_dir, "unlensed_data_strain.tmp.npy")
tmp_h    = os.path.join(tmp_dir, "unlensed_h_strain.tmp.npy")
tmp_t    = os.path.join(tmp_dir, "unlensed_time_array.tmp.npy")
tmp_snr_single = os.path.join(tmp_dir, "unlensed_optimal_SNR_single.tmp.npy")
tmp_snr_net    = os.path.join(tmp_dir, "unlensed_optimal_SNR_network.tmp.npy")

for p in [tmp_data, tmp_h, tmp_t, tmp_snr_single, tmp_snr_net]:
    if os.path.exists(p):
        os.remove(p)

# shape(n_events, n_ifos, N)
data_whiten_mm = np.lib.format.open_memmap(
    tmp_data, mode="w+", dtype=np.float64, shape=(n_events, n_ifos, N)
)
h_whiten_mm = np.lib.format.open_memmap(
    tmp_h, mode="w+", dtype=np.float64, shape=(n_events, n_ifos, N)
)
t_mm = np.lib.format.open_memmap(
    tmp_t, mode="w+", dtype=np.float64, shape=(n_events, n_ifos, N)
)

# 每个探测器各自的optimal SNR
snr_single_mm = np.lib.format.open_memmap(
    tmp_snr_single, mode="w+", dtype=np.float64, shape=(n_events, n_ifos)
)

# 总SNR
snr_net_mm = np.lib.format.open_memmap(
    tmp_snr_net, mode="w+", dtype=np.float64, shape=(n_events,)
)


for i in range(n_events):

    injection_parameters = source_params.iloc[i].to_dict()

    r = 1500


    # 先生成一次频域波形，后面每个探测器共用
    fd_waveform = waveform_generator.frequency_domain_strain(injection_parameters)

    snr_sq_network = 0.0

    for j, ifo in enumerate(ifos):

        # 为当前探测器生成噪声
        ifo.set_strain_data_from_power_spectral_density(
            sampling_frequency=sampling_frequency,
            duration=duration,
            start_time=injection_parameters["geocent_time"] - (N-r) / sampling_frequency)

        n_t = ifo.strain_data.time_domain_strain.copy()
        t_array = ifo.strain_data.time_array.copy()

        n_f_white = ifo.whitened_frequency_domain_strain
        n_t_white = np.fft.irfft(n_f_white, n=N)

        # 当前探测器响应
        response = ifo.get_detector_response(fd_waveform, injection_parameters)
        snr_squared = np.real(ifo.optimal_snr_squared(response))
        snr = np.sqrt(np.abs(snr_squared))

        snr_single_mm[i, j] = snr
        snr_sq_network += np.abs(snr_squared)

        # 注入信号
        ifo.inject_signal(
            waveform_generator=waveform_generator,
            parameters=injection_parameters
        , raise_error=False)

        d_t = ifo.strain_data.time_domain_strain.copy()

        d_f_white = ifo.whitened_frequency_domain_strain
        d_t_white = np.fft.irfft(d_f_white, n=N)

        h_t = d_t - n_t
        h_t_white = d_t_white - n_t_white



        # 信号h(t)在峰值后0.05秒处进行切除，并使用Hanning窗平滑过渡到零
        peak_index = np.argmax(np.abs(h_t_white))

        cut_index = peak_index + int(0.05 * sampling_frequency)
        cut_index = min(cut_index, N)

        h_t_white_new = h_t_white.copy()

        fade_len = N - cut_index
        if fade_len > 0:
            hann_full = np.hanning(2 * fade_len)
            fade_window = hann_full[fade_len:]
            h_t_white_new[cut_index:] *= fade_window

        d_t_white_new = h_t_white_new + n_t_white



        # 保存
        t_mm[i, j, :] = t_array
        data_whiten_mm[i, j, :] = d_t_white_new
        h_whiten_mm[i, j, :] = h_t_white_new

    # 保存网络SNR
    snr_net_mm[i] = np.sqrt(snr_sq_network)

# flush
data_whiten_mm.flush()
h_whiten_mm.flush()
t_mm.flush()
snr_single_mm.flush()
snr_net_mm.flush()

# 最终文件名
final_data = "unlensed_data_strain.npy"
final_h    = "unlensed_h_strain.npy"
final_t    = "unlensed_time_array.npy"
final_snr_single = "unlensed_optimal_SNR_single.npy"
final_snr_net    = "unlensed_optimal_SNR_network.npy"

for p in [final_data, final_h, final_t, final_snr_single, final_snr_net]:
    if os.path.exists(p):
        os.remove(p)

shutil.move(tmp_data, final_data)
shutil.move(tmp_h, final_h)
shutil.move(tmp_t, final_t)
shutil.move(tmp_snr_single, final_snr_single)
shutil.move(tmp_snr_net, final_snr_net)
