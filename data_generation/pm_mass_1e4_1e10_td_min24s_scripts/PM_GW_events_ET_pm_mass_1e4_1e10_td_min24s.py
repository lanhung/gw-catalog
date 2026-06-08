#!/usr/bin/env python3
# Auto-generated from PM GW events.ipynb
# Detector branch: ET

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
RUN_NAME = os.environ.get("GW_RUN_NAME", "PM_GW_events_ET_pm_mass_1e4_1e10_td_min24s")
output_dir = os.path.join(OUTPUT_ROOT, RUN_NAME)
os.makedirs(output_dir, exist_ok=True)

# Keep all relative CSV/NPY outputs for this run under one directory.
os.chdir(output_dir)
tmp_dir = os.path.join(output_dir, "tmp")
os.makedirs(tmp_dir, exist_ok=True)
print(f"Writing outputs to: {output_dir}")

# %% Cell 2
# random seed

n=613 #lensed

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

# %% Cell 6
#透镜化样本个数（小于等于 n_samples）
n_lens=10000

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


MIN_TIME_DELAY_SECONDS = 24.0
MAX_LENS_REJECTION_ATTEMPTS = 100000
rejected_time_delay = 0
rejected_magnification = 0

for i in range(n_lens):
    # 源红移
    dL = lensed_source_1.iloc[i]['luminosity_distance']
    z_s = luminosity_distance_to_redshift(dL)

    # 透镜红移（这里取源红移的一半）
    z_l = z_s / 2

    # 在生成阶段直接拒绝 t_d < 24s 或任一像实际放大率 abs(mu) < 1 的 PM 透镜参数。
    for attempt in range(1, MAX_LENS_REJECTION_ATTEMPTS + 1):
        # 透镜质量(太阳质量)
        m_l = np.random.uniform(1e4, 1e10)*ms  # PM扩展质量范围：10^4-10^10 M_sun

        lens_cosmo = LensCosmo(z_lens=z_l, z_source=z_s, cosmo=cosmo)
        Dls=(lens_cosmo.dds*units.Mpc).to(units.m).value
        Dl=(lens_cosmo.dd*units.Mpc).to(units.m).value
        Ds=(lens_cosmo.ds*units.Mpc).to(units.m).value

        # Einstein radius (arcsec)
        theta_E = np.sqrt((4*G*m_l/c**2)*(Dls/(Dl*Ds)))*(180*3600/np.pi)

        y = np.random.uniform(0.01, 0.3)   # 不大于0.3，保证第二个像放大率 > 1
        phi= np.random.uniform(0, 2*np.pi)
        beta_x= y*theta_E* np.cos(phi)
        beta_y= y*theta_E* np.sin(phi)

        mu_plus=1/2+(y**2+2)/(2*y*np.sqrt(y**2+4))
        mu_minus=1/2-(y**2+2)/(2*y*np.sqrt(y**2+4))

        t_d=4*G*m_l*(1+z_l)*c**(-3)*(0.5*y*np.sqrt(y**2+4)+np.log((np.sqrt(y**2+4)+y)/(np.sqrt(y**2+4)-y)))
        time_delay_ok = t_d >= MIN_TIME_DELAY_SECONDS
        magnification_ok = (abs(mu_plus) >= 1.0) and (abs(mu_minus) >= 1.0)
        if time_delay_ok and magnification_ok:
            break
        if not time_delay_ok:
            rejected_time_delay += 1
        if not magnification_ok:
            rejected_magnification += 1
    else:
        raise RuntimeError(f'Failed to sample PM lens with t_d >= {MIN_TIME_DELAY_SECONDS}s and abs(mu)>=1 for index {i}')

    print('z_s =', z_s)
    print('z_l =', z_l)
    print('m_l =', m_l)
    print('theta_E =', theta_E)
    print('y =', y)
    print('beta_x =', beta_x)
    print('beta_y =', beta_y)
    print(mu_plus, mu_minus)
    print(t_d,'s','=',t_d/(24*3600),'days')
    print('time_delay_rejection_attempts_for_this_sample =', attempt - 1)
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

print("Total rejected PM lens samples with t_d <", MIN_TIME_DELAY_SECONDS, "s:", rejected_time_delay)
print("Total rejected PM lens samples with abs(mu) < 1:", rejected_magnification)

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


tmp_data_1 = os.path.join(tmp_dir, "PM_data_strain_1.tmp.npy")
tmp_h_1    = os.path.join(tmp_dir, "PM_h_strain_1.tmp.npy")
tmp_t_1    = os.path.join(tmp_dir, "PM_time_array_1.tmp.npy")
tmp_snr_1  = os.path.join(tmp_dir, "PM_optimal_SNR_1.tmp.npy")

for p in [tmp_data_1, tmp_h_1, tmp_t_1, tmp_snr_1]:
    if os.path.exists(p):
        os.remove(p)

data_whiten_mm_1 = np.lib.format.open_memmap(
    tmp_data_1, mode="w+", dtype=np.float64, shape=(n_events, N))
h_whiten_mm_1 = np.lib.format.open_memmap(
    tmp_h_1, mode="w+", dtype=np.float64, shape=(n_events, N))
t_mm_1 = np.lib.format.open_memmap(
    tmp_t_1, mode="w+", dtype=np.float64, shape=(n_events, N))
snr_mm_1 = np.lib.format.open_memmap(
    tmp_snr_1, mode="w+", dtype=np.float64, shape=(n_events,))


ET_0 = bilby.gw.detector.InterferometerList(['ET'])[0]  # 只使用一个探测器ET

# 读取每一组参数，计算对应的引力波信号
for i in range(n_events):

    # 取出一组参数
    injection_parameters = {**lensed_source_params.iloc[i].to_dict(),   # 将第 i 行转换为字典
                            **lens.iloc[i].to_dict(),
                            'which_image':0}

    r=1500

    fd_waveform = waveform_generator_lensed.frequency_domain_strain(injection_parameters)

    ET_0.set_strain_data_from_power_spectral_density(
        sampling_frequency=sampling_frequency,
        duration=duration,
        start_time=injection_parameters["geocent_time"] - (N-r) / sampling_frequency)

    n_t=ET_0.strain_data.time_domain_strain
    t_array=ET_0.strain_data.time_array

    n_f_white = ET_0.whitened_frequency_domain_strain
    n_t_white = np.fft.irfft(n_f_white, n=N)


    response = ET_0.get_detector_response(fd_waveform, injection_parameters)
    snr_squared = ET_0.optimal_snr_squared(response)
    snr = np.abs(np.sqrt(snr_squared))

    ET_0.inject_signal(waveform_generator=waveform_generator_lensed,
                        parameters=injection_parameters, raise_error=False)

    d_t=ET_0.strain_data.time_domain_strain

    d_f_white = ET_0.whitened_frequency_domain_strain
    d_t_white = np.fft.irfft(d_f_white, n=N)

    h_t=d_t-n_t
    h_t_white=d_t_white-n_t_white



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



    t_mm_1[i, :] = t_array
    snr_mm_1[i] = snr
    data_whiten_mm_1[i, :] = d_t_white_new
    h_whiten_mm_1[i, :] = h_t_white_new

data_whiten_mm_1.flush()
h_whiten_mm_1.flush()
t_mm_1.flush()
snr_mm_1.flush()

final_data_1 = "PM_data_strain_1.npy"
final_h_1  = "PM_h_strain_1.npy"
final_t_1   = "PM_time_array_1.npy"
final_snr_1 = "PM_optimal_SNR_1.npy"

for p in [final_data_1, final_h_1, final_t_1, final_snr_1]:
    if os.path.exists(p):
        os.remove(p)

shutil.move(tmp_data_1, final_data_1)
shutil.move(tmp_h_1, final_h_1)
shutil.move(tmp_t_1, final_t_1)
shutil.move(tmp_snr_1, final_snr_1)

# %% Cell 32
bilby.core.utils.random.seed(n+2)

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


tmp_data_2 = os.path.join(tmp_dir, "PM_data_strain_2.tmp.npy")
tmp_h_2    = os.path.join(tmp_dir, "PM_h_strain_2.tmp.npy")
tmp_t_2    = os.path.join(tmp_dir, "PM_time_array_2.tmp.npy")
tmp_snr_2  = os.path.join(tmp_dir, "PM_optimal_SNR_2.tmp.npy")

for p in [tmp_data_2, tmp_h_2, tmp_t_2, tmp_snr_2]:
    if os.path.exists(p):
        os.remove(p)

data_whiten_mm_2 = np.lib.format.open_memmap(
    tmp_data_2, mode="w+", dtype=np.float64, shape=(n_events, N))
h_whiten_mm_2 = np.lib.format.open_memmap(
    tmp_h_2, mode="w+", dtype=np.float64, shape=(n_events, N))
t_mm_2 = np.lib.format.open_memmap(
    tmp_t_2, mode="w+", dtype=np.float64, shape=(n_events, N))
snr_mm_2 = np.lib.format.open_memmap(
    tmp_snr_2, mode="w+", dtype=np.float64, shape=(n_events,))


ET_0 = bilby.gw.detector.InterferometerList(['ET'])[0]  # 只使用一个探测器ET

# 读取每一组参数，计算对应的引力波信号
for i in range(n_events):

    # 取出一组参数
    injection_parameters = {**lensed_source_params.iloc[i+(len(lensed_source_params)//2)].to_dict(),   # 将第 i 行转换为字典
                            **lens.iloc[i].to_dict(),
                            'which_image':1}

    r=1500

    fd_waveform = waveform_generator_lensed.frequency_domain_strain(injection_parameters)

    ET_0.set_strain_data_from_power_spectral_density(
        sampling_frequency=sampling_frequency,
        duration=duration,
        start_time=injection_parameters["geocent_time"] - (N-r) / sampling_frequency)

    n_t=ET_0.strain_data.time_domain_strain
    t_array=ET_0.strain_data.time_array

    n_f_white = ET_0.whitened_frequency_domain_strain
    n_t_white = np.fft.irfft(n_f_white, n=N)



    response = ET_0.get_detector_response(fd_waveform, injection_parameters)
    snr_squared = ET_0.optimal_snr_squared(response)
    snr = np.abs(np.sqrt(snr_squared))

    ET_0.inject_signal(waveform_generator=waveform_generator_lensed,
                        parameters=injection_parameters, raise_error=False)

    d_t=ET_0.strain_data.time_domain_strain

    d_f_white = ET_0.whitened_frequency_domain_strain
    d_t_white = np.fft.irfft(d_f_white, n=N)

    h_t=d_t-n_t
    h_t_white=d_t_white-n_t_white

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



    t_mm_2[i, :] = t_array
    snr_mm_2[i] = snr
    data_whiten_mm_2[i, :] = d_t_white_new
    h_whiten_mm_2[i, :] = h_t_white_new


data_whiten_mm_2.flush()
h_whiten_mm_2.flush()
t_mm_2.flush()
snr_mm_2.flush()

final_data_2 = "PM_data_strain_2.npy"
final_h_2   = "PM_h_strain_2.npy"
final_t_2   = "PM_time_array_2.npy"
final_snr_2 = "PM_optimal_SNR_2.npy"

for p in [final_data_2, final_h_2, final_t_2, final_snr_2]:
    if os.path.exists(p):
        os.remove(p)

shutil.move(tmp_data_2, final_data_2)
shutil.move(tmp_h_2, final_h_2)
shutil.move(tmp_t_2, final_t_2)
shutil.move(tmp_snr_2, final_snr_2)

# %% Cell 34+ removed: ET test/noisy waveform NPY generation is not needed for 10000 run.
