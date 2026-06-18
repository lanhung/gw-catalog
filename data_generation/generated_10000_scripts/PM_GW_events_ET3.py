#!/usr/bin/env python3
# Auto-generated from PM GW events.ipynb
# Detector branch: ET three-arm

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
import sys
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_generation.detector_network import DetectorNetworkSpec, build_interferometers, interferometer_names, simulate_detector_network

# 在系统临时文件夹中创建临时文件
tmp_dir = tempfile.gettempdir()

# 宇宙学模型
bilby.gw.cosmology.DEFAULT_COSMOLOGY=cosmo
bilby.gw.cosmology.COSMOLOGY = [cosmo, cosmo.name]
bilby.gw.cosmology.get_cosmology()  # 查看默认宇宙学模型

# Output path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUTPUT_ROOT = os.environ.get("GW_OUTPUT_ROOT", os.path.join(SCRIPT_DIR, "outputs"))
RUN_NAME = os.environ.get("GW_RUN_NAME", "PM_GW_events_ET3")
output_dir = os.path.join(OUTPUT_ROOT, RUN_NAME)
os.makedirs(output_dir, exist_ok=True)

# Keep all relative CSV/NPY outputs for this run under one directory.
os.chdir(output_dir)
tmp_dir = os.path.join(output_dir, "tmp")
os.makedirs(tmp_dir, exist_ok=True)
print(f"Writing outputs to: {output_dir}")

# Detector network configuration. Defaults reproduce ET three-arm generation.
DETECTOR_SPEC = DetectorNetworkSpec.from_string(
    os.environ.get("GW_DETECTOR_NETWORK", "ET"),
    max_channels=int(os.environ.get("GW_DETECTOR_CHANNELS", "3")),
)


# %% Cell 2
# random seed

n=613 #lensed

# %% Cell 4
# 总样本个数
n_samples=int(os.environ.get("GW_N_SAMPLES", "10000"))

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

# %% Cell 6
#透镜化样本个数（小于等于 n_samples）
n_lens=min(int(os.environ.get("GW_N_LENS", str(n_samples))), n_samples)

# %% Cell 8
sampling_frequency=4096  # f_s >= 2*f_max   #
duration=24  # len(strain_data) = f_s*duration
minimum_frequency=20.0

# %% Cell 10
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

# %% Cell 12
source_params=pd.read_csv('source_samples.csv')

np.random.seed(n)
idx = np.random.choice(n_samples, n_lens, replace=False)
idx = np.sort(idx)

print(idx)
idx={'lensed_index': idx}
lensed_index=pd.DataFrame(idx)
lensed_index.to_csv('lensed_index.csv', index=False)
lensed_index

lensed_source_1 = source_params.iloc[lensed_index['lensed_index']]
lensed_source_1

# %% Cell 15
np.random.seed(n)
rng = np.random.default_rng(n)
ms=const.M_sun.to(units.kg).value  # 太阳质量(kg)
G=const.G.value  # gravitational constant (m3 kg-1 s-2)
c=const.c.value  # speed of light (m/s)


tmp_params = os.path.join(tmp_dir, "lens_params.tmp.csv")
tmp_lens   = os.path.join(tmp_dir, "lens.tmp.csv")

for p in [tmp_params, tmp_lens]:
    if os.path.exists(p):
        os.remove(p)

pd.DataFrame(columns=["z_l",
                      "z_s",
                      "m_l",
                      "theta_E(arcsec)",
                      "y",
                      "beta_x",
                      "beta_y"]).to_csv(tmp_params, index=False)

pd.DataFrame(columns=["mu_0",
                      "mu_1",
                      "t_d"]).to_csv(tmp_lens, index=False)


for i in range(n_lens):
    # 源红移
    dL = lensed_source_1.iloc[i]['luminosity_distance']
    z_s = luminosity_distance_to_redshift(dL)

    # 透镜红移（这里取源红移的一半）
    z_l = z_s / 2

    # 透镜质量(太阳质量)
    m_l = np.random.uniform(1e8, 1e10)*ms  # 对应SMBH，且保证时延在s量级，可区分两像

    lens_cosmo = LensCosmo(z_lens=z_l, z_source=z_s, cosmo=cosmo)
    Dls=(lens_cosmo.dds*units.Mpc).to(units.m).value
    Dl=(lens_cosmo.dd*units.Mpc).to(units.m).value
    Ds=(lens_cosmo.ds*units.Mpc).to(units.m).value

    # Einstein radius (arcsec)
    theta_E = np.sqrt((4*G*m_l/c**2)*(Dls/(Dl*Ds)))*(180*3600/np.pi)

    print('z_s =', z_s)
    print('z_l =', z_l)
    print('m_l =', m_l)
    print('theta_E =', theta_E)


    y = np.random.uniform(0.01, 0.3)   # 不大于0.3，保证第二个像放大率 > 1
    phi= np.random.uniform(0, 2*np.pi)
    beta_x= y*theta_E* np.cos(phi)
    beta_y= y*theta_E* np.sin(phi)

    print('y =', y)
    print('beta_x =', beta_x)
    print('beta_y =', beta_y)

    mu_plus=1/2+(y**2+2)/(2*y*np.sqrt(y**2+4))
    mu_minus=1/2-(y**2+2)/(2*y*np.sqrt(y**2+4))

    t_d=4*G*m_l*(1+z_l)*c**(-3)*(0.5*y*np.sqrt(y**2+4)+np.log((np.sqrt(y**2+4)+y)/(np.sqrt(y**2+4)-y)))
    print(mu_plus, mu_minus)
    print(t_d,'s','=',t_d/(24*3600),'days')
    print()

    row_0 = pd.DataFrame([{
        "z_l": z_l,
        "z_s": z_s,
        "m_l": m_l/ms,
        "theta_E(arcsec)": theta_E,
        "y": y,
        "beta_x": beta_x,
        "beta_y": beta_y}])

    row_1 = pd.DataFrame([{
        "mu_0": mu_plus,
        "mu_1": mu_minus,
        "t_d": t_d}])

    row_0.to_csv(tmp_params, mode="a", header=False, index=False)
    row_1.to_csv(tmp_lens,   mode="a", header=False, index=False)


final_params = "lens_params.csv"
final_lens = "lens.csv"

for p in [final_params, final_lens]:
    if os.path.exists(p):
        os.remove(p)

shutil.move(tmp_params, final_params)
shutil.move(tmp_lens, final_lens)

# %% Cell 17
lens=pd.read_csv('lens.csv')

t_d=[]
for i in range(len(lens)):
    t_d.append((lens['t_d'][i]))
print(t_d)

original_times = lensed_source_1['geocent_time'].values
# print(original_times)

geocent_time_2 = original_times + t_d
# print(geocent_time_2)

lensed_source_2 = lensed_source_1.copy()
lensed_source_2['geocent_time'] = geocent_time_2

lensed_source_params = pd.concat([lensed_source_1, lensed_source_2], axis=0, ignore_index=False)
lensed_source_params.to_csv('lensed_source_samples.csv', index=False)

lensed_source_params

# %% Cell 19 removed: ET test/noisy source CSV generation is not needed for 10000 run.

# %% Cell 21
def lens_PM_ampfac(mu_0, mu_1, t_d, frequencies, which_image):

    mu = np.array([mu_0, mu_1])
    n = np.array([0, 1/2])

    if which_image == 0:
        i = 0

    elif which_image == 1:
        i = 1

    else:
        raise ValueError("which_image should be either 0 or 1")

    # 不再加入时延,由注入的geocent_time控制
    F = np.sqrt(np.abs(mu[i])) * np.exp(-1j * np.pi * n[i])

    return {
        'F': F,
        'mu': mu[i],
        't_d': t_d,
        'n': n[i]}


def lensed_waveform_F(frequency_array, mass_1, mass_2, a_1, a_2, tilt_1, tilt_2, phi_12, phi_jl,
                    luminosity_distance, theta_jn, psi, phase, geocent_time, ra, dec,
                    mu_0, mu_1, t_d, which_image,**kwargs):

    # GW waveform
    params = {
        'mass_1': mass_1, 'mass_2': mass_2, 'a_1': a_1, 'a_2': a_2,
        'tilt_1': tilt_1, 'tilt_2': tilt_2, 'phi_12': phi_12, 'phi_jl': phi_jl,
        'luminosity_distance': luminosity_distance, 'theta_jn': theta_jn,
        'psi': psi, 'phase': phase, 'geocent_time': geocent_time,
        'ra': ra, 'dec': dec}

    h = bilby.gw.source.lal_binary_black_hole(frequency_array,**params,**kwargs)

    z_s = luminosity_distance_to_redshift(luminosity_distance)
    print('z_s:', z_s)

    F = lens_PM_ampfac(mu_0, mu_1, t_d, frequency_array, which_image)
    print('mu:', F['mu'])
    print('time delay(s):', str(F['t_d'])+' s'+' = '+str(F['t_d']/(24*60*60))+' days')
    print('Morse indice:', F['n'])
    print()

    return {'plus': h['plus'] * F['F'], 'cross': h['cross'] * F['F']}

# %% Cell 27
bilby.core.utils.random.seed(n+1)

N = sampling_frequency*duration

waveform_arguments = dict(waveform_approximant='IMRPhenomXPHM',
                          reference_frequency=10., minimum_frequency=minimum_frequency)

# lensed_waveform
waveform_generator_lensed=bilby.gw.waveform_generator.WaveformGenerator(
    sampling_frequency=sampling_frequency,
    duration=duration,
    frequency_domain_source_model=lensed_waveform_F,
    parameter_conversion=bilby.gw.conversion.convert_to_lal_binary_black_hole_parameters,
    waveform_arguments=waveform_arguments)



lensed_source_params=pd.read_csv('lensed_source_samples.csv')
lens = pd.read_csv('lens.csv')
n_events = len(lensed_source_params)//2




def generate_lensed_image(which_image, source_offset, seed_offset):
    bilby.core.utils.random.seed(n + seed_offset)
    ifos = build_interferometers(bilby, DETECTOR_SPEC)
    n_ifos = len(ifos)
    suffix = which_image + 1
    print(f"Using detector channels for image {suffix}: {interferometer_names(ifos)}")

    tmp_data = os.path.join(tmp_dir, f"PM_data_strain_{suffix}.tmp.npy")
    tmp_h = os.path.join(tmp_dir, f"PM_h_strain_{suffix}.tmp.npy")
    tmp_t = os.path.join(tmp_dir, f"PM_time_array_{suffix}.tmp.npy")
    tmp_snr_single = os.path.join(tmp_dir, f"PM_optimal_SNR_single_{suffix}.tmp.npy")
    tmp_snr_net = os.path.join(tmp_dir, f"PM_optimal_SNR_network_{suffix}.tmp.npy")
    tmp_snr_compat = os.path.join(tmp_dir, f"PM_optimal_SNR_{suffix}.tmp.npy")

    for p in [tmp_data, tmp_h, tmp_t, tmp_snr_single, tmp_snr_net, tmp_snr_compat]:
        if os.path.exists(p):
            os.remove(p)

    data_whiten_mm = np.lib.format.open_memmap(tmp_data, mode="w+", dtype=np.float64, shape=(n_events, n_ifos, N))
    h_whiten_mm = np.lib.format.open_memmap(tmp_h, mode="w+", dtype=np.float64, shape=(n_events, n_ifos, N))
    t_mm = np.lib.format.open_memmap(tmp_t, mode="w+", dtype=np.float64, shape=(n_events, n_ifos, N))
    snr_single_mm = np.lib.format.open_memmap(tmp_snr_single, mode="w+", dtype=np.float64, shape=(n_events, n_ifos))
    snr_net_mm = np.lib.format.open_memmap(tmp_snr_net, mode="w+", dtype=np.float64, shape=(n_events,))
    snr_compat_mm = np.lib.format.open_memmap(tmp_snr_compat, mode="w+", dtype=np.float64, shape=(n_events,))

    for i in range(n_events):
        injection_parameters = {**lensed_source_params.iloc[i + source_offset].to_dict(), **lens.iloc[i].to_dict(), 'which_image': which_image}
        r = 1500
        fd_waveform = waveform_generator_lensed.frequency_domain_strain(injection_parameters)
        data_arr, h_arr, t_arr, snr_single, snr_network = simulate_detector_network(
            ifos, waveform_generator_lensed, fd_waveform, injection_parameters, sampling_frequency, duration, N, r
        )
        t_mm[i, :, :] = t_arr
        snr_single_mm[i, :] = snr_single
        snr_net_mm[i] = snr_network
        snr_compat_mm[i] = snr_network
        data_whiten_mm[i, :, :] = data_arr
        h_whiten_mm[i, :, :] = h_arr

    data_whiten_mm.flush(); h_whiten_mm.flush(); t_mm.flush(); snr_single_mm.flush(); snr_net_mm.flush(); snr_compat_mm.flush()

    final_data = f"PM_data_strain_{suffix}.npy"
    final_h = f"PM_h_strain_{suffix}.npy"
    final_t = f"PM_time_array_{suffix}.npy"
    final_snr_single = f"PM_optimal_SNR_single_{suffix}.npy"
    final_snr_net = f"PM_optimal_SNR_network_{suffix}.npy"
    final_snr_compat = f"PM_optimal_SNR_{suffix}.npy"

    for p in [final_data, final_h, final_t, final_snr_single, final_snr_net, final_snr_compat]:
        if os.path.exists(p):
            os.remove(p)

    shutil.move(tmp_data, final_data)
    shutil.move(tmp_h, final_h)
    shutil.move(tmp_t, final_t)
    shutil.move(tmp_snr_single, final_snr_single)
    shutil.move(tmp_snr_net, final_snr_net)
    shutil.move(tmp_snr_compat, final_snr_compat)


generate_lensed_image(which_image=0, source_offset=0, seed_offset=1)
generate_lensed_image(which_image=1, source_offset=len(lensed_source_params)//2, seed_offset=2)

# %% Cell 34+ removed: ET test/noisy waveform NPY generation is not needed for 10000 run.
