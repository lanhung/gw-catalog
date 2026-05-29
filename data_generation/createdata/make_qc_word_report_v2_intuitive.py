
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from html import escape
import struct
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

ROOT = Path('generated_10000_20260527_091859')
BASE = ROOT / 'qc_showcase_adaptive_peak'
OUT = ROOT / 'qc_word_report_v2_intuitive'
OUT.mkdir(exist_ok=True)

LENSED = {
    ('PM', 'ET'): ROOT / 'PM_GW_events_ET_10000',
    ('PM', 'LIGO'): ROOT / 'PM_GW_events_LIGO_10000',
    ('SIS', 'ET'): ROOT / 'SIS_GW_events_ET_10000',
    ('SIS', 'LIGO'): ROOT / 'SIS_GW_events_LIGO_10000',
}
UNLENSED = {'ET': ROOT / 'unlensed_GW_events_ET_10000', 'LIGO': ROOT / 'unlensed_GW_events_LIGO_10000'}

plt.rcParams.update({
    'font.size': 9,
    'axes.titlesize': 10,
    'axes.labelsize': 9,
    'legend.fontsize': 7,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.22,
})

def load(p): return np.load(p, mmap_mode='r')
def finite(x):
    x = np.asarray(x, dtype=float).ravel()
    return x[np.isfinite(x)]
def pclip(vals, lo=0.5, hi=99.0):
    vals = finite(vals)
    return np.percentile(vals, lo), np.percentile(vals, hi)
def clipped(vals, lo, hi):
    vals = finite(vals)
    return vals[(vals >= lo) & (vals <= hi)], int(np.sum(vals > hi)), int(np.sum(vals < lo))
def note(ax, text, loc='upper right'):
    pos = {'upper right': (0.98,0.96,'right','top'), 'upper left': (0.02,0.96,'left','top'), 'lower right': (0.98,0.04,'right','bottom')}
    x,y,ha,va = pos[loc]
    ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va, fontsize=8, bbox=dict(facecolor='white', alpha=0.78, edgecolor='none', pad=2))


READABLE = {
    'mu_0': 'A image magnification',
    '|mu_1|': 'B image magnification',
    'mu_total': 'Total magnification',
    'm_l': 'PM lens mass',
    'sigma_v': 'SIS velocity dispersion',
    'y': 'Source position y',
    'z_l': 'Lens redshift',
    'z_s': 'Source redshift',
    'mass_1_source': 'Primary black-hole mass',
    'mass_2_source': 'Secondary black-hole mass',
    'luminosity_distance': 'Luminosity distance',
    'a_1': 'Primary spin magnitude',
    'a_2': 'Secondary spin magnitude',
    'theta_jn': 'Viewing angle',
    'ra': 'Right ascension',
    'dec': 'Declination',
    'psi': 'Polarization angle',
    'phase': 'Coalescence phase',
    'tilt_1': 'Primary spin tilt',
    'tilt_2': 'Secondary spin tilt',
    'phi_12': 'Spin azimuth phi_12',
    'phi_jl': 'Spin azimuth phi_jl',
    'geocent_time': 'Event time',
}

def nice(name):
    return READABLE.get(name, name)

def snr_series(detector):
    series = []
    for model in ['PM','SIS']:
        d = LENSED[(model, detector)]
        if detector == 'ET':
            series += [(f'{model} A image (earlier arrival)', finite(load(d/f'{model}_optimal_SNR_1.npy'))), (f'{model} B image (delayed arrival)', finite(load(d/f'{model}_optimal_SNR_2.npy')))]
        else:
            series += [(f'{model} A image network SNR', finite(load(d/f'{model}_optimal_SNR_network_1.npy'))), (f'{model} B image network SNR', finite(load(d/f'{model}_optimal_SNR_network_2.npy')))]
    if detector == 'ET':
        series.append(('Unlensed signal', finite(load(UNLENSED[detector]/'unlensed_optimal_SNR.npy'))))
    else:
        series.append(('Unlensed network SNR', finite(load(UNLENSED[detector]/'unlensed_optimal_SNR_network.npy'))))
    return series

# Copy/keep Fig1 but make a smaller single-page version by cropping axes via existing generated png is already good.
if (BASE/'Fig1_lensed_pair_example_adaptive_peak.png').exists():
    (OUT/'Fig1_lensed_pair_example_adaptive_peak.png').write_bytes((BASE/'Fig1_lensed_pair_example_adaptive_peak.png').read_bytes())

# Fig2: more intuitive SNR: compact hist + box summary per detector.
fig = plt.figure(figsize=(12.2, 7.2), constrained_layout=True)
gs = GridSpec(2, 2, figure=fig, height_ratios=[2.2, 1.0])
colors = ['tab:blue','tab:cyan','tab:green','tab:olive','tab:orange']
for col, detector in enumerate(['ET','LIGO']):
    series = snr_series(detector)
    allv = np.concatenate([v for _,v in series])
    lo, hi = 0, max(np.percentile(allv, 99), 12)
    ax = fig.add_subplot(gs[0,col])
    bins = np.linspace(lo, hi, 72)
    for (label, vals), c in zip(series, colors):
        vals_c, n_hi, _ = clipped(vals, lo, hi)
        ax.hist(vals_c, bins=bins, histtype='step', lw=1.4, label=label, color=c)
    ax.axvspan(0, 8, color='tab:red', alpha=0.07, label='SNR < 8')
    ax.axvline(8, color='tab:red', ls='--', lw=1)
    ax.axvline(10, color='tab:orange', ls=':', lw=1)
    ax.set_xlim(lo, hi)
    ax.set_title(f'{detector}: SNR distribution, p99 display range')
    ax.set_xlabel('optimal SNR')
    ax.set_ylabel('count')
    note(ax, f'x-axis clipped at p99\n>{hi:.1f}: {int(np.sum(allv>hi))}/{len(allv)} samples')
    ax.legend(ncol=1, loc='upper left', bbox_to_anchor=(1.01, 1.0), frameon=True, borderaxespad=0.0)
    axb = fig.add_subplot(gs[1,col])
    data = [np.clip(vals, lo, hi) for _, vals in series]
    axb.boxplot(data, vert=False, labels=[s[0] for s in series], showfliers=False, patch_artist=True,
                boxprops=dict(facecolor='lightgray', alpha=0.75), medianprops=dict(color='black'))
    axb.axvline(8, color='tab:red', ls='--', lw=1)
    axb.axvline(10, color='tab:orange', ls=':', lw=1)
    axb.set_xlim(lo, hi)
    axb.set_xlabel('optimal SNR, clipped at p99')
fig.suptitle('Fig2 Signal strength (SNR): distribution and percentile summary', fontsize=13)
fig.savefig(OUT/'Fig2_SNR_distribution_intuitive.png', dpi=180)
fig.savefig(OUT/'Fig2_SNR_distribution_intuitive.pdf')
plt.close(fig)

# Fig3: magnification, log-x compact view to avoid empty tail and label overlap.
fig, axes = plt.subplots(2, 3, figsize=(13.2, 6.4), constrained_layout=True)
for row, model in enumerate(['PM','SIS']):
    lens = pd.read_csv(LENSED[(model,'ET')]/'lens.csv')
    vals_list = [lens['mu_0'].to_numpy(), np.abs(lens['mu_1'].to_numpy()), np.abs(lens['mu_0'].to_numpy()) + np.abs(lens['mu_1'].to_numpy())]
    titles = ['A image magnification', 'B image magnification', 'Total magnification']
    for col, (ax, vals, title) in enumerate(zip(axes[row], vals_list, titles)):
        vals = finite(vals)
        lo = max(np.percentile(vals, 0.2), 1e-3)
        hi = np.percentile(vals, 99.0)
        vals_c, n_hi, n_lo = clipped(vals, lo, hi)
        bins = np.logspace(np.log10(lo), np.log10(hi), 58)
        color = 'tab:blue' if model == 'PM' else 'tab:green'
        ax.hist(vals_c, bins=bins, color=color, alpha=0.78)
        ax.set_xscale('log')
        med = np.median(vals)
        ax.axvline(med, color='black', ls='--', lw=1.1)
        if title == 'Total magnification':
            ax.axvline(2, color='tab:red', ls=':', lw=1.2)
            threshold_text = 'check line: total=2'
        else:
            ax.axvline(1, color='tab:red', ls=':', lw=1.2)
            threshold_text = 'reference line: magnification=1'
        ax.set_xlim(lo, hi)
        ax.set_title(f'{model} {title}', pad=8)
        ax.set_xlabel(title)
        ax.set_ylabel('count')
        # Put summary and clipping notes in opposite corners to avoid overlap, especially in the third column.
        note(ax, f'median={med:.2g}\n{threshold_text}', 'upper left')
        note(ax, f'xmax=p99={hi:.2g}\n>{hi:.2g}: {n_hi}/{len(vals)}', 'lower right')
fig.suptitle('Fig3 Lensing magnification: compact log scale for A image, B image, and total', fontsize=13)
fig.savefig(OUT/'Fig3_magnification_distribution_intuitive.png', dpi=180)
fig.savefig(OUT/'Fig3_magnification_distribution_intuitive.pdf')
plt.close(fig)

# Fig4: time delay with log scale to remove empty long-tail space.
fig, axes = plt.subplots(2, 3, figsize=(12.2, 6.2), constrained_layout=True)
for row, model in enumerate(['PM','SIS']):
    d = LENSED[(model,'ET')]
    lens = pd.read_csv(d/'lens.csv')
    params = pd.read_csv(d/'lens_params.csv')
    dt = finite(lens['t_d'])
    bins = np.logspace(np.log10(dt.min()), np.log10(dt.max()), 72)
    axes[row,0].hist(dt, bins=bins, color='tab:purple', alpha=0.78)
    axes[row,0].set_xscale('log')
    axes[row,0].axvline(np.median(dt), color='black', ls='--', lw=1.1)
    axes[row,0].set_title(f'{model} time-delay distribution')
    axes[row,0].set_xlabel('Time delay between A and B [s], log scale')
    axes[row,0].set_ylabel('count')
    note(axes[row,0], f'median={np.median(dt):.2g}s\nmax={dt.max():.2g}s', 'upper left')
    xcol = 'm_l' if model == 'PM' else 'sigma_v'
    xlabel = nice(xcol)
    axes[row,1].scatter(params[xcol], dt, s=3, alpha=0.22, color='tab:blue')
    axes[row,1].set_yscale('log')
    if model == 'PM': axes[row,1].set_xscale('log')
    axes[row,1].set_title(f'Time delay vs {xlabel}')
    axes[row,1].set_xlabel(xlabel)
    axes[row,1].set_ylabel('Time delay [s], log')
    axes[row,2].scatter(params['y'], dt, s=3, alpha=0.22, color='tab:green')
    axes[row,2].set_yscale('log')
    axes[row,2].set_title('Time delay vs source position')
    axes[row,2].set_xlabel('Source position y')
fig.suptitle('Fig4 Time delay between A and B images', fontsize=13)
fig.savefig(OUT/'Fig4_time_delay_distribution_intuitive.png', dpi=180)
fig.savefig(OUT/'Fig4_time_delay_distribution_intuitive.pdf')
plt.close(fig)

# Fig5: lens parameters, compact p0.5-p99.5.
fig, axes = plt.subplots(2, 4, figsize=(13.2, 5.8), constrained_layout=True)
for row, model in enumerate(['PM','SIS']):
    params = pd.read_csv(LENSED[(model,'ET')]/'lens_params.csv')
    cols = ['m_l' if model=='PM' else 'sigma_v', 'y', 'z_l', 'z_s']
    for ax, col in zip(axes[row], cols):
        vals = finite(params[col])
        lo, hi = np.percentile(vals, [0.5, 99.5])
        vc, nhi, nlo = clipped(vals, lo, hi)
        ax.hist(vc, bins=58, color='tab:cyan', alpha=0.82)
        ax.axvline(np.median(vals), color='black', ls='--', lw=1.1)
        ax.set_xlim(lo, hi)
        ax.set_title(f'{model} {nice(col)}')
        note(ax, f'median={np.median(vals):.2g}', 'upper left')
fig.suptitle('Fig5 Lens-parameter distributions', fontsize=13)
fig.savefig(OUT/'Fig5_lens_parameter_distribution_intuitive.png', dpi=180)
fig.savefig(OUT/'Fig5_lens_parameter_distribution_intuitive.pdf')
plt.close(fig)

# Fig6 source params: exact grids, compact p0.5-p99.5.
source_sets = {
    'PM lensed': pd.read_csv(LENSED[('PM','ET')]/'source_samples.csv'),
    'SIS lensed': pd.read_csv(LENSED[('SIS','ET')]/'source_samples.csv'),
    'unlensed': pd.read_csv(UNLENSED['ET']/ 'source_samples.csv'),
}
colors = {'PM lensed':'tab:blue', 'SIS lensed':'tab:green', 'unlensed':'tab:orange'}
groups = [
    ('mass_distance', 'Fig6a GW source masses and distance', ['mass_1_source','mass_2_source','luminosity_distance'], (11.2,3.0)),
    ('spin_orientation', 'Fig6b GW source spins and viewing angle', ['a_1','a_2','theta_jn'], (11.2,3.0)),
    ('sky_phase', 'Fig6c GW source sky position and phase', ['ra','dec','psi','phase'], (12.2,3.0)),
    ('spin_angles_time', 'Fig6d GW source spin angles and event time', ['tilt_1','tilt_2','phi_12','phi_jl','geocent_time'], (13.6,3.0)),
]
for suffix, title, cols, size in groups:
    fig, axes = plt.subplots(1, len(cols), figsize=size, constrained_layout=True)
    if len(cols) == 1: axes = [axes]
    for ax, col in zip(axes, cols):
        allv = np.concatenate([finite(df[col]) for df in source_sets.values()])
        lo, hi = np.percentile(allv, [0.5, 99.5])
        bins = np.linspace(lo, hi, 56)
        for name, df in source_sets.items():
            vals = finite(df[col])
            vals = vals[(vals >= lo) & (vals <= hi)]
            ax.hist(vals, bins=bins, histtype='step', lw=1.25, density=True, color=colors[name], label=name)
        ax.set_title(nice(col))
        ax.set_yticks([])
    axes[-1].legend(loc='upper right', fontsize=7, frameon=True)
    fig.suptitle(title, fontsize=12)
    fig.savefig(OUT/f'Fig6_GW_source_parameter_distribution_{suffix}_intuitive.png', dpi=180)
    fig.savefig(OUT/f'Fig6_GW_source_parameter_distribution_{suffix}_intuitive.pdf')
    plt.close(fig)

# Docx builder.
sections = [
    ('Fig1 代表性双像波形', OUT/'Fig1_lensed_pair_example_adaptive_peak.png', '用来看同一个源的 A 像（先到达）和 B 像（后到达）在峰值附近是否形态相似，峰值和幅度是否正常。'),
    ('Fig2 信号强度 SNR 分布', OUT/'Fig2_SNR_distribution_intuitive.png', '用来看 ET 和 LIGO 里信号强弱的整体分布，以及有多少样本超过 SNR=8 或 SNR=10。'),
    ('Fig3 透镜放大率分布', OUT/'Fig3_magnification_distribution_intuitive.png', '用来看 A 像和 B 像的放大率以及总放大率是否合理，确认样本是否处在强放大双像区域。'),
    ('Fig4 A/B 像时间延迟分布', OUT/'Fig4_time_delay_distribution_intuitive.png', '用来看 A 像和 B 像之间的时间延迟是否为正、数量级是否合理，以及它和透镜参数的关系。'),
    ('Fig5 透镜模型参数分布', OUT/'Fig5_lens_parameter_distribution_intuitive.png', '用来看 PM 和 SIS 透镜模型的参数采样范围是否符合设定。'),
    ('Fig6a 引力波源质量和距离分布', OUT/'Fig6_GW_source_parameter_distribution_mass_distance_intuitive.png', '用来看生成引力波源时的质量和距离分布是否正常。'),
    ('Fig6b 引力波源自旋和观测角分布', OUT/'Fig6_GW_source_parameter_distribution_spin_orientation_intuitive.png', '用来看黑洞自旋大小和观测倾角的采样分布。'),
    ('Fig6c 引力波源天空位置和相位分布', OUT/'Fig6_GW_source_parameter_distribution_sky_phase_intuitive.png', '用来看天空位置、偏振角和相位角是否覆盖完整范围。'),
    ('Fig6d 引力波源自旋角和事件时间分布', OUT/'Fig6_GW_source_parameter_distribution_spin_angles_time_intuitive.png', '用来看自旋方向角和事件时间的采样分布是否正常。'),
]
W_NS='http://schemas.openxmlformats.org/wordprocessingml/2006/main'; R_NS='http://schemas.openxmlformats.org/officeDocument/2006/relationships'; WP_NS='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'; A_NS='http://schemas.openxmlformats.org/drawingml/2006/main'; PIC_NS='http://schemas.openxmlformats.org/drawingml/2006/picture'
def p_xml(text='', style=None):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
    return f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'
def png_size(path):
    data = path.read_bytes()[:24]
    return struct.unpack('>II', data[16:24]) if data[:8] == b'\x89PNG\r\n\x1a\n' else (1200,800)
def image_xml(rid, cx, cy, name, docpr_id):
    return f'<w:p><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="{WP_NS}"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{docpr_id}" name="{escape(name)}"/><a:graphic xmlns:a="{A_NS}"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="{PIC_NS}"><pic:nvPicPr><pic:cNvPr id="0" name="{escape(name)}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
body=[p_xml('引力波生成结果 QC 图表说明（优化版）','Title'), p_xml('本版图像减少空白、压缩长尾显示，并在每张图下面保留一句简单说明。')]
rels=[]; media=[]; ridn=1; docid=1
for title, img, desc in sections:
    body.append(p_xml(title,'Heading1'))
    if img.exists():
        rid=f'rId{ridn}'; ridn+=1; m=f'image{ridn-1}.png'; rels.append((rid,m)); media.append((m,img.read_bytes()))
        w,h=png_size(img); cx=int(6.35*914400); cy=int(cx*h/w)
        body.append(image_xml(rid,cx,cy,img.name,docid)); docid+=1
    body.append(p_xml(desc))
sect='<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="800" w:right="800" w:bottom="800" w:left="800" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
document_xml=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}"><w:body>{"".join(body)}{sect}</w:body></w:document>'
styles_xml=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="{W_NS}"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Arial" w:eastAsia="SimSun" w:hAnsi="Arial"/><w:sz w:val="21"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:jc w:val="center"/><w:spacing w:after="160"/></w:pPr><w:rPr><w:b/><w:rFonts w:ascii="Arial" w:eastAsia="SimHei" w:hAnsi="Arial"/><w:sz w:val="32"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="180" w:after="90"/></w:pPr><w:rPr><w:b/><w:rFonts w:ascii="Arial" w:eastAsia="SimHei" w:hAnsi="Arial"/><w:sz w:val="24"/></w:rPr></w:style></w:styles>'
ct='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'
root_rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
docrels=['<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>']+[f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{m}"/>' for rid,m in rels]
doc_rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(docrels)+'</Relationships>'
with ZipFile(OUT/'引力波生成结果_QC图表说明_优化版.docx','w',ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml',ct); z.writestr('_rels/.rels',root_rels); z.writestr('word/_rels/document.xml.rels',doc_rels); z.writestr('word/document.xml',document_xml); z.writestr('word/styles.xml',styles_xml)
    for m,data in media: z.writestr(f'word/media/{m}',data)
md=['# 引力波生成结果 QC 图表说明（优化版）','']
for title,img,desc in sections: md += [f'## {title}','',f'图片：{img.name}','',desc,'']
(OUT/'引力波生成结果_QC图表说明_优化版.md').write_text('\n'.join(md), encoding='utf-8')
print(OUT)
