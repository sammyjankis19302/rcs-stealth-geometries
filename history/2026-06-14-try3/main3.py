"""
main3.py
========
Full-physics comparative analysis using solvers_v2.py

  Fig 10 — Physics level comparison: PO vs PO+PTD vs Full (PO+PTD+DB)
            on both conventional and stealth aircraft
  Fig 11 — Contribution breakdown: how much each mechanism contributes
            at every azimuth angle
  Fig 12 — RAM material comparison: Salisbury screen vs Dallenbach layers
            (3 presets) vs bare metal, full frequency sweep
  Fig 13 — Edge map: visualise which edges contribute most to RCS
            (edge colour = diffraction strength)
  Fig 14 — Double bounce hotspot map: which facet PAIRS cause corner
            reflector enhancement on conventional vs stealth
"""

import os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs
from matplotlib.colors import Normalize, LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/claude/rcs_project')
from geometries import conventional_aircraft, stealth_aircraft
from solvers_v2 import (DoubleBounce, PTDSolver, POAmplitudeSolver,
                         SalisburyScreen, DallenbachLayer,
                         physics_frequency_sweep, breakdown_sweep,
                         mie_rcs_dbsm)

OUT = './output'
os.makedirs(OUT, exist_ok=True)

# ── Design tokens ──────────────────────────────────────────────────────────
BG     = '#080C14'
PANEL  = '#0E1420'
GRID_C = '#1E2A3A'
TEXT   = '#D0DCF0'
DIM    = '#6A7A9A'
C_CONV  = '#FF5B35'
C_STLTH = '#00E5FF'
C_PO    = '#888888'
C_PTD   = '#FFD040'
C_DB    = '#C084FC'
C_FULL  = '#00FF88'

RADAR_CMAP = LinearSegmentedColormap.from_list(
    'radar', ['#080C14','#0A2040','#004080','#0080C0',
               '#00C0E0','#40E080','#C0E040','#FFB000','#FF4000'])

FREQ_HZ  = 10e9
FREQ_GHZ = 10.0
FREQS    = np.linspace(1e9, 36e9, 100)
FREQS_G  = FREQS / 1e9

def set_bg(fig, axes=None):
    fig.patch.set_facecolor(BG)
    if axes is not None:
        for ax in (axes.flat if hasattr(axes, 'flat') else axes):
            try: ax.set_facecolor(PANEL)
            except: pass

def style_ax(ax, xlabel='', ylabel='', title=''):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=DIM, labelsize=8)
    ax.xaxis.label.set_color(DIM); ax.xaxis.label.set_size(9)
    ax.yaxis.label.set_color(DIM); ax.yaxis.label.set_size(9)
    ax.set_title(title, color=TEXT, fontsize=10, fontweight='bold', pad=6)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.grid(color=GRID_C, linewidth=0.6, linestyle='--', alpha=0.8)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_C)

def style_polar(ax, title='', r_min=-50, r_max=50):
    ax.set_facecolor(PANEL)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_ylim(r_min, r_max)
    ax.set_title(title, color=TEXT, fontsize=9, fontweight='bold', pad=10)
    ax.tick_params(colors=DIM, labelsize=7)
    ax.grid(color=GRID_C, linewidth=0.5, alpha=0.7)
    ax.spines['polar'].set_color(GRID_C)
    ax.set_yticks(np.arange(r_min, r_max+1, 10))
    ax.set_yticklabels([f'{t}' for t in np.arange(r_min, r_max+1, 10)], color=DIM, fontsize=6)
    ax.set_xticklabels(['N\n0°','45°','E\n90°','135°','S\n180°','225°','W\n270°','315°'],
                        fontsize=7, color=DIM)

print("Building geometries …")
V_C, F_C = conventional_aircraft()
V_S, F_S = stealth_aircraft()
print(f"  Conventional : {len(F_C)} facets, {len(PTDSolver(V_C,F_C,FREQ_HZ).edges)} edges")
print(f"  Stealth      : {len(F_S)} facets, {len(PTDSolver(V_S,F_S,FREQ_HZ).edges)} edges")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 10 — PHYSICS LEVEL COMPARISON
# ═════════════════════════════════════════════════════════════════════════════

print("\nFig 10: Physics level comparison …")

N_AZ = 180
az_angles = np.linspace(0, 360, N_AZ, endpoint=False)
az_rad    = np.radians(az_angles)

levels = [('PO only', 'po', C_PO, '--'),
          ('PO + PTD', 'ptd', C_PTD, '-.'),
          ('Full (PO+PTD+DB)', 'full', C_FULL, '-')]

print("  Conventional …")
rcs_conv = {}
for label, lvl, color, ls in levels:
    print(f"    {label} …")
    s = []; solver = None
    for az in az_angles:
        if solver is None or True:
            pass
        tmp = __import__('solvers_v2', fromlist=['make_solver'])
        sol = tmp.make_solver(V_C, F_C, FREQ_HZ, level=lvl)
        s.append(sol.monostatic_rcs_dbsm(az))
    rcs_conv[label] = np.array(s)

print("  Stealth …")
rcs_stlth = {}
for label, lvl, color, ls in levels:
    print(f"    {label} …")
    s = []
    for az in az_angles:
        tmp = __import__('solvers_v2', fromlist=['make_solver'])
        sol = tmp.make_solver(V_S, F_S, FREQ_HZ, level=lvl)
        s.append(sol.monostatic_rcs_dbsm(az))
    rcs_stlth[label] = np.array(s)

# More efficient version: build solvers once
print("  (rebuilding efficiently) …")
solvers_conv  = {lvl: __import__('solvers_v2',fromlist=['make_solver']).make_solver(V_C,F_C,FREQ_HZ,level=lvl)
                  for _, lvl, _, _ in levels}
solvers_stlth = {lvl: __import__('solvers_v2',fromlist=['make_solver']).make_solver(V_S,F_S,FREQ_HZ,level=lvl)
                  for _, lvl, _, _ in levels}
for label, lvl, color, ls in levels:
    rcs_conv[label]  = np.array([solvers_conv[lvl].monostatic_rcs_dbsm(az)  for az in az_angles])
    rcs_stlth[label] = np.array([solvers_stlth[lvl].monostatic_rcs_dbsm(az) for az in az_angles])

r_min = min(min(v.min() for v in rcs_conv.values()),
             min(v.min() for v in rcs_stlth.values())) - 3
r_max = max(max(v.max() for v in rcs_conv.values()),
             max(v.max() for v in rcs_stlth.values())) + 3

fig10, axes = plt.subplots(1, 2, figsize=(18, 8),
                             subplot_kw={'projection': 'polar'}, facecolor=BG)
set_bg(fig10)

for ax, title, rcs_dict, base_c in [
        (axes[0], 'CONVENTIONAL AIRCRAFT', rcs_conv,  C_CONV),
        (axes[1], 'STEALTH AIRCRAFT',       rcs_stlth, C_STLTH)]:
    style_polar(ax, title, r_min=r_min, r_max=r_max)
    for label, lvl, color, ls in levels:
        ax.plot(az_rad, rcs_dict[label], color=color, lw=1.8, ls=ls,
                label=label, alpha=0.95)
    ax.legend(loc='lower right', bbox_to_anchor=(1.4, -0.05),
               fontsize=9, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)

fig10.suptitle(f"Physics Level Comparison  |  {FREQ_GHZ:.0f} GHz  |  "
                "Azimuth Sweep at El=0°\n"
                "Grey=PO only  ·  Yellow=PO+PTD  ·  Green=Full (PO+PTD+DouBounce)",
                color=TEXT, fontsize=12, fontweight='bold', y=1.02)

# Annotation: key differences
for ax, rcs_dict in [(axes[0], rcs_conv), (axes[1], rcs_stlth)]:
    delta_ptd  = rcs_dict['PO + PTD'].mean()  - rcs_dict['PO only'].mean()
    delta_db   = rcs_dict['Full (PO+PTD+DB)'].mean() - rcs_dict['PO + PTD'].mean()
    ax.set_title(ax.get_title() +
                  f"\nPTD adds {delta_ptd:+.1f} dB mean  |  DB adds {delta_db:+.1f} dB mean",
                  color=TEXT, fontsize=9, fontweight='bold', pad=12)

plt.tight_layout()
fig10.savefig(f'{OUT}/fig10_physics_levels.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig10)
print("  → fig10_physics_levels.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 11 — CONTRIBUTION BREAKDOWN BY MECHANISM
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 11: Contribution breakdown …")

print("  Conventional breakdown sweep …")
bd_conv  = breakdown_sweep(V_C, F_C, FREQ_HZ, n=N_AZ)
print("  Stealth breakdown sweep …")
bd_stlth = breakdown_sweep(V_S, F_S, FREQ_HZ, n=N_AZ)

fig11, axes = plt.subplots(2, 3, figsize=(20, 11), facecolor=BG)
set_bg(fig11, axes)
fig11.suptitle(f"RCS Contribution Breakdown by Scattering Mechanism  |  {FREQ_GHZ:.0f} GHz",
                color=TEXT, fontsize=13, fontweight='bold', y=0.98)

mech_cols = [
    ('PO only',       C_PO,    'Specular (facet reflection)'),
    ('PTD edge',      C_PTD,   'Edge diffraction (PTD fringe)'),
    ('Double bounce', C_DB,    'Double bounce (corner reflector)'),
]

for col, (key, color, full_label) in enumerate(mech_cols):
    for row, (bd, aircraft, ac_color) in enumerate([
            (bd_conv,  'Conventional', C_CONV),
            (bd_stlth, 'Stealth',      C_STLTH)]):
        ax = axes[row, col]
        style_ax(ax, 'Azimuth (°)', 'RCS (dBsm)',
                  f"{aircraft}  —  {full_label}")
        ax.plot(bd['angles'], bd[key], color=color, lw=1.8)
        ax.fill_between(bd['angles'], bd[key], bd[key].min()-5,
                         color=color, alpha=0.15)
        ax.plot(bd['angles'], bd['Full (PO+PTD+DB)'], color='white',
                lw=0.8, ls=':', alpha=0.4, label='Full total')
        ax.set_xlim(0, 360)
        # Mark peak
        pk_idx = np.argmax(bd[key])
        ax.axvline(bd['angles'][pk_idx], color=color, lw=0.8, ls='--', alpha=0.5)
        ax.text(bd['angles'][pk_idx]+2, bd[key][pk_idx],
                f"peak\n{bd[key][pk_idx]:.1f} dBsm",
                color=color, fontsize=7)
        ax.set_title(f"{aircraft} — {key}", color=ac_color,
                      fontsize=10, fontweight='bold')

plt.tight_layout(rect=[0, 0, 1, 0.96])
fig11.savefig(f'{OUT}/fig11_breakdown.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig11)
print("  → fig11_breakdown.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 12 — RAM MATERIAL FREQUENCY RESPONSE
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 12: RAM material comparison …")

# Build RAM models
ram_models = {
    'Salisbury f₀=10GHz (d=7.5mm)': SalisburyScreen(10e9),
    'Salisbury f₀=15GHz (d=5.0mm)': SalisburyScreen(15e9),
    'Dallenbach: Carbon foam  5mm':  DallenbachLayer.from_preset('carbon_foam',   0.005),
    'Dallenbach: Carbonyl iron 5mm': DallenbachLayer.from_preset('carbonyl_iron', 0.005),
    'Dallenbach: Ferrite tile 5mm':  DallenbachLayer.from_preset('ferrite_tile',  0.005),
}
ram_colors = ['#FFD040', '#FFA040', '#7CFC00', '#00E5FF', '#C084FC']

fig12 = plt.figure(figsize=(20, 10), facecolor=BG)
grid12 = gs.GridSpec(2, 3, figure=fig12, hspace=0.42, wspace=0.35,
                      left=0.06, right=0.97, top=0.92, bottom=0.08)
fig12.suptitle("Radar Absorbing Material (RAM)  |  Physics-Based Frequency Response",
                color=TEXT, fontsize=13, fontweight='bold')

# --- RAM absorption curves ---
ax_abs = fig12.add_subplot(grid12[0, :2])
style_ax(ax_abs, 'Frequency (GHz)', 'One-way absorption (dB)',
          'RAM Absorption vs Frequency  (0 dB = bare metal, more negative = more absorbed)')
for (name, model), color in zip(ram_models.items(), ram_colors):
    ab = model.absorption_db(FREQS)
    ax_abs.plot(FREQS_G, ab, color=color, lw=2, label=name)
ax_abs.axhline(-10, color=DIM, lw=0.7, ls='--')
ax_abs.text(35.5, -10, '−10 dB\nthreshold', color=DIM, fontsize=7, va='center')
ax_abs.set_xlim(1, 36); ax_abs.set_ylim(-35, 1)
ax_abs.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C,
               loc='lower right')

# Add X-band highlight
ax_abs.axvspan(8, 12, color='#1A2E44', alpha=0.5)
ax_abs.text(10, -33, 'X-band', color='#3A6A9A', fontsize=9,
             ha='center', fontweight='bold')

# --- RCS vs frequency: Stealth + best RAM ---
ax_rcs = fig12.add_subplot(grid12[0, 2])
style_ax(ax_rcs, 'Frequency (GHz)', 'RCS (dBsm)',
          'Stealth A/C Nose-on RCS\n+ Various RAM')
rcs_bare = physics_frequency_sweep(V_S, F_S, FREQS, 0.0, level='full')
ax_rcs.plot(FREQS_G, rcs_bare, color='white', lw=1.5, label='Bare metal')
for (name, model), color in zip(ram_models.items(), ram_colors):
    rcs_ram = physics_frequency_sweep(V_S, F_S, FREQS, 0.0, level='full',
                                       ram_model=model)
    short_name = name.split(':')[-1].strip().split('(')[0].strip()[:20]
    ax_rcs.plot(FREQS_G, rcs_ram, color=color, lw=1.5, label=short_name)
ax_rcs.set_xlim(1, 36)
ax_rcs.legend(fontsize=7, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)

# --- Salisbury screen physics diagram ---
ax_diag = fig12.add_subplot(grid12[1, 0])
ax_diag.set_facecolor(PANEL)
ax_diag.set_title("Salisbury Screen Structure", color=TEXT,
                    fontsize=10, fontweight='bold', pad=8)
ax_diag.set_xlim(0, 10); ax_diag.set_ylim(0, 10)
ax_diag.axis('off')

# Draw layers
layers = [
    (8.5, 9.2, '#3A6A9A', 'Resistive sheet  Rₛ = Z₀ = 377 Ω/□'),
    (5.0, 8.0, '#1A2E44', 'Lossless spacer  d = λ₀/4'),
    (2.5, 4.5, '#444',    'PEC ground plane'),
]
for y0, y1, fc, label in layers:
    ax_diag.fill_between([1, 9], [y0, y0], [y1, y1], color=fc, alpha=0.7)
    ax_diag.text(5, (y0+y1)/2, label, ha='center', va='center',
                  color=TEXT, fontsize=8, fontweight='bold')

# Incident and reflected arrows
ax_diag.annotate('', xy=(3, 8.5), xytext=(1.5, 9.8),
                  arrowprops=dict(color='#3B8BD4', lw=2, arrowstyle='->', connectionstyle='arc3,rad=0'))
ax_diag.text(1.2, 9.9, 'Eᵢ', color='#3B8BD4', fontsize=10)
ax_diag.annotate('', xy=(5, 9.8), xytext=(3.5, 8.5),
                  arrowprops=dict(color='#E24B4A', lw=1.5, arrowstyle='->', connectionstyle='arc3,rad=0'))
ax_diag.text(5.2, 9.9, 'Eᵣ → 0 at f₀', color='#E24B4A', fontsize=9)
ax_diag.text(5, 0.5, 'Eᵣ = 0  when  d = λ₀/4  and  Rₛ = Z₀',
              ha='center', color=DIM, fontsize=8)

# --- Dallenbach layer physics diagram ---
ax_diag2 = fig12.add_subplot(grid12[1, 1])
ax_diag2.set_facecolor(PANEL)
ax_diag2.set_title("Dallenbach Layer Structure", color=TEXT,
                     fontsize=10, fontweight='bold', pad=8)
ax_diag2.set_xlim(0, 10); ax_diag2.set_ylim(0, 10)
ax_diag2.axis('off')

ax_diag2.fill_between([1, 9], [5, 5], [8.5, 8.5], color='#2A4A2A', alpha=0.7)
ax_diag2.text(5, 6.75, 'Lossy slab\nεᵣ = ε′−jε″,  μᵣ = μ′−jμ″\nthickness d',
               ha='center', va='center', color=TEXT, fontsize=8, fontweight='bold')
ax_diag2.fill_between([1, 9], [3.5, 3.5], [4.8, 4.8], color='#444', alpha=0.8)
ax_diag2.text(5, 4.15, 'PEC ground plane', ha='center', va='center',
               color=TEXT, fontsize=8, fontweight='bold')

# Equations
ax_diag2.text(5, 2.5, 'γ = j(2πf/c)√(μᵣ εᵣ)', ha='center', color=C_PTD, fontsize=8)
ax_diag2.text(5, 1.7, 'Z_m = Z₀√(μᵣ/εᵣ)',      ha='center', color=C_PTD, fontsize=8)
ax_diag2.text(5, 0.9, 'Z_in = Z_m tanh(γd)',     ha='center', color=C_PTD, fontsize=8)
ax_diag2.text(5, 0.1, 'Γ = (Z_in−Z₀)/(Z_in+Z₀)',ha='center', color=C_FULL, fontsize=8)

ax_diag2.annotate('', xy=(3, 8.5), xytext=(1.5, 9.5),
                   arrowprops=dict(color='#3B8BD4', lw=2, arrowstyle='->'))
ax_diag2.text(1.2, 9.6, 'Eᵢ', color='#3B8BD4', fontsize=10)

# --- Total reduction summary table ---
ax_sum = fig12.add_subplot(grid12[1, 2])
ax_sum.set_facecolor(PANEL)
ax_sum.set_title("Total RCS Reduction at X-band  (Nose-on, Stealth A/C)",
                  color=TEXT, fontsize=9, fontweight='bold', pad=8)
ax_sum.axis('off')

idx10 = np.argmin(np.abs(FREQS_G - 10))
rows_sum = [('Conventional bare metal', rcs_bare[idx10] + 12, C_CONV)]   # offset for reference
rows_sum = [('Stealth bare metal', rcs_bare[idx10], 'white')]
for (name, model), color in zip(ram_models.items(), ram_colors):
    rcs_r = physics_frequency_sweep(V_S, F_S, FREQS, 0.0, level='full', ram_model=model)
    rows_sum.append((name.split(':')[-1].strip()[:25], rcs_r[idx10], color))

baseline = rows_sum[0][1]
y = 0.92
ax_sum.text(0.0,  y, 'Configuration',  color=DIM, fontsize=9, fontweight='bold',
             transform=ax_sum.transAxes)
ax_sum.text(0.72, y, 'RCS (dBsm)',    color=DIM, fontsize=9, fontweight='bold',
             transform=ax_sum.transAxes)
ax_sum.text(0.88, y, 'vs bare',       color=DIM, fontsize=9, fontweight='bold',
             transform=ax_sum.transAxes)
y -= 0.07
for name, val, color in rows_sum:
    delta = val - baseline
    ax_sum.add_patch(plt.Rectangle((0, y-0.045), 1, 0.08, transform=ax_sum.transAxes,
                      facecolor=color, alpha=0.08))
    ax_sum.text(0.0,  y, name[:28],       color=color, fontsize=8,
                 transform=ax_sum.transAxes, va='center')
    ax_sum.text(0.72, y, f'{val:.1f}',    color=TEXT, fontsize=8,
                 transform=ax_sum.transAxes, va='center')
    ax_sum.text(0.88, y, f'{delta:+.1f}', color=C_FULL if delta < 0 else C_CONV,
                 fontsize=8, transform=ax_sum.transAxes, va='center')
    y -= 0.13

fig12.savefig(f'{OUT}/fig12_ram_physics.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig12)
print("  → fig12_ram_physics.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 13 — EDGE MAP  (colour edges by diffraction contribution strength)
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 13: Edge diffraction map …")

def edge_strengths(solver, az_deg=0.0, el_deg=0.0):
    """Return per-edge diffraction amplitude magnitude at given look angle."""
    shat  = solver._shat(az_deg, el_deg)
    strengths = []
    for i in range(len(solver.edges)):
        ê        = solver.edge_dir[i]
        L        = solver.edge_L[i]
        c        = solver.edge_c[i]
        n        = solver.edge_n[i]
        cos_beta = abs(ê @ shat)
        sin_beta = np.sqrt(max(0.0, 1.0 - cos_beta**2))
        D        = solver._D_fringe(n, sin_beta)
        sinc_v   = float(np.abs(_sinc(solver.k * L * cos_beta))) if sin_beta > 0.02 else 0.0
        strengths.append(abs(D) * L * sinc_v)
    return np.array(strengths)

def _sinc(x):
    return np.where(np.abs(x) < 1e-9, 1.0, np.sin(x) / x)

ptd_c = PTDSolver(V_C, F_C, FREQ_HZ)
ptd_s = PTDSolver(V_S, F_S, FREQ_HZ)

# Compute edge strengths at nose-on (0°) and broadside (90°)
angles_map = [(0, 'Nose-on  (0°)'), (90, 'Broadside  (90°)')]

fig13, axes = plt.subplots(2, 4, figsize=(22, 10), facecolor=BG,
                             gridspec_kw={'width_ratios': [1,1,1,1]})
set_bg(fig13, axes)
fig13.suptitle("Edge Diffraction Map  |  Edge Colour = PTD Contribution Strength",
                color=TEXT, fontsize=13, fontweight='bold', y=0.98)

cmap_edge = LinearSegmentedColormap.from_list('edge',
    ['#1A2A1A','#00AA44','#FFD040','#FF4400'])

view_angles = [(25, -145), (10, -80), (40, -120), (15, -45)]

for row, (solver, V, F, ac_name, ac_color) in enumerate([
        (ptd_c, V_C, F_C, 'CONVENTIONAL', C_CONV),
        (ptd_s, V_S, F_S, 'STEALTH',      C_STLTH)]):

    # Compute edge strengths at two aspect angles
    str_nose    = edge_strengths(solver, 0.0)
    str_broad   = edge_strengths(solver, 90.0)
    str_combined = str_nose + str_broad
    vmax = str_combined.max() + 1e-10

    for col in range(4):
        ax = axes[row, col]
        ax.set_facecolor(BG)

        if col < 2:
            # 3D edge-coloured plot
            az_label = ['Nose-on  (0°)', 'Broadside  (90°)'][col]
            str_use   = [str_nose, str_broad][col]

            ax3 = fig13.add_subplot(2, 4, row*4 + col + 1, projection='3d')
            ax3.set_facecolor(BG)
            for pane in [ax3.xaxis.pane, ax3.yaxis.pane, ax3.zaxis.pane]:
                pane.fill = False; pane.set_edgecolor('#1A2434')
            ax3.tick_params(colors='#2A3A50', labelsize=5)

            # Draw facets (faint)
            tris = [V[f] for f in F]
            poly = Poly3DCollection(tris, alpha=0.15, facecolor=ac_color,
                                     edgecolor='none')
            ax3.add_collection3d(poly)

            # Draw edges coloured by strength
            norm_e = Normalize(vmin=0, vmax=vmax)
            for i, (v0_i, v1_i, _) in enumerate(solver.edges):
                p0 = V[v0_i]; p1 = V[v1_i]
                strength = str_use[i]
                rgba = cmap_edge(norm_e(strength))
                lw = 0.5 + 3.0 * norm_e(strength)
                ax3.plot([p0[0], p1[0]], [p0[1], p1[1]], [p0[2], p1[2]],
                          color=rgba, lw=lw, alpha=0.9)

            margin = 0.3
            ax3.set_xlim(V[:,0].min()-margin, V[:,0].max()+margin)
            ax3.set_ylim(V[:,1].min()-margin, V[:,1].max()+margin)
            ax3.set_zlim(V[:,2].min()-margin, V[:,2].max()+margin)
            ax3.view_init(elev=view_angles[col][0], azim=view_angles[col][1])
            ax3.set_title(f"{ac_name}  —  {az_label}\nWarm = stronger edge diffraction",
                           color=ac_color, fontsize=8, fontweight='bold', pad=4)

        elif col == 2:
            # Edge strength bar chart (sorted)
            ax.set_facecolor(PANEL)
            sorted_idx  = np.argsort(str_combined)[::-1][:12]
            bar_colors  = [cmap_edge(v / (vmax+1e-10)) for v in str_combined[sorted_idx]]
            ax.barh(range(len(sorted_idx)), str_combined[sorted_idx],
                     color=bar_colors, alpha=0.85)
            ax.set_yticks(range(len(sorted_idx)))
            ax.set_yticklabels([f'Edge {i}' for i in sorted_idx], color=DIM, fontsize=7)
            ax.tick_params(colors=DIM, labelsize=7)
            ax.set_xlabel('PTD strength (a.u.)', color=DIM, fontsize=8)
            ax.set_title(f'{ac_name}\nTop-12 Edges', color=ac_color,
                          fontsize=9, fontweight='bold')
            ax.set_facecolor(PANEL)
            for spine in ax.spines.values(): spine.set_edgecolor(GRID_C)
            ax.grid(color=GRID_C, lw=0.5, axis='x')

        elif col == 3:
            # n_wedge distribution
            ax.set_facecolor(PANEL)
            n_vals = solver.edge_n
            ax.hist(n_vals, bins=15, color=ac_color, alpha=0.7, edgecolor=GRID_C)
            ax.axvline(1.5, color=C_DB,    lw=1.5, ls='--', label='90° ridge (n=1.5)')
            ax.axvline(2.0, color=C_PTD,   lw=1.5, ls='--', label='Half-plane (n=2.0)')
            ax.axvline(2.5, color='#FF4444',lw=1.5, ls='--', label='Concave (n=2.5)')
            ax.tick_params(colors=DIM, labelsize=7)
            ax.set_xlabel('Wedge parameter n', color=DIM, fontsize=8)
            ax.set_ylabel('Edge count', color=DIM, fontsize=8)
            ax.set_title(f'{ac_name}\nWedge angle distribution', color=ac_color,
                          fontsize=9, fontweight='bold')
            for spine in ax.spines.values(): spine.set_edgecolor(GRID_C)
            ax.grid(color=GRID_C, lw=0.5)
            ax.legend(fontsize=7, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)

plt.tight_layout(rect=[0, 0, 1, 0.95])
fig13.savefig(f'{OUT}/fig13_edge_map.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig13)
print("  → fig13_edge_map.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 14 — DOUBLE BOUNCE HOTSPOT MAP
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 14: Double bounce hotspot map …")

def double_bounce_matrix(vertices, faces, frequency_hz, az_deg=90.0):
    """N×N matrix of double-bounce RCS contribution between each facet pair."""
    solver = DoubleBounce(vertices, faces, frequency_hz)
    shat   = solver._shat(az_deg, 0.0)
    N      = len(faces)
    mat    = np.zeros((N, N))

    cos_theta = solver.normals @ shat
    illum     = cos_theta > 1e-6

    for i in np.where(illum)[0]:
        n_i   = solver.normals[i]
        c_i   = solver.centroids[i]
        A_i   = solver.areas[i]
        ct_i  = cos_theta[i]
        s_ref = shat - 2.0*(n_i@shat)*n_i
        s_ref /= (np.linalg.norm(s_ref) + 1e-30)

        for j in range(N):
            if j == i: continue
            n_j      = solver.normals[j]
            c_j      = solver.centroids[j]
            A_j      = solver.areas[j]
            cos_j_r  = n_j @ s_ref
            cos_j_rx = n_j @ shat
            if cos_j_r < 1e-6 or cos_j_rx < 1e-6: continue
            amp = A_i * ct_i * A_j * cos_j_r * cos_j_rx
            mat[i, j] = amp

    return mat

print("  Conventional @ 90° …")
db_mat_c = double_bounce_matrix(V_C, F_C, FREQ_HZ, 90.0)
print("  Stealth @ 90° …")
db_mat_s = double_bounce_matrix(V_S, F_S, FREQ_HZ, 90.0)

fig14, axes = plt.subplots(1, 2, figsize=(16, 7), facecolor=BG)
set_bg(fig14, axes)
fig14.suptitle("Double-Bounce Hotspot Matrix  |  Broadside 90°  |  "
                "Each cell = how strongly facet i reflects onto facet j",
                color=TEXT, fontsize=12, fontweight='bold', y=1.01)

for ax, mat, title, ac_color in [
        (axes[0], db_mat_c, 'CONVENTIONAL AIRCRAFT', C_CONV),
        (axes[1], db_mat_s, 'STEALTH AIRCRAFT',       C_STLTH)]:
    im = ax.imshow(mat, cmap=RADAR_CMAP, aspect='auto')
    ax.set_title(title, color=ac_color, fontsize=12, fontweight='bold', pad=8)
    ax.set_xlabel('Secondary facet j  (receiver)', color=DIM, fontsize=9)
    ax.set_ylabel('Primary facet i  (first bounce)', color=DIM, fontsize=9)
    ax.tick_params(colors=DIM, labelsize=8)
    plt.colorbar(im, ax=ax, label='Amplitude contribution (a.u.)',
                  fraction=0.046, pad=0.04).ax.yaxis.label.set_color(DIM)
    # Annotate hotspots
    if mat.max() > 0:
        hi = np.unravel_index(mat.argmax(), mat.shape)
        ax.plot(hi[1], hi[0], 'w*', ms=14)
        ax.text(hi[1]+0.3, hi[0]-0.5,
                f'Hotspot\ni={hi[0]} → j={hi[1]}\namp={mat[hi]:.3f}',
                color='white', fontsize=8,
                bbox=dict(facecolor='#0A0E1A', alpha=0.7, pad=3))

# Physical interpretation text
fig14.text(0.5, -0.04,
    "Bright off-diagonal cells = facet i specularly redirects energy onto facet j → retroreflection back to radar.\n"
    "Conventional aircraft: bright clusters near fin/fuselage junction (high i, high j index = tail region).\n"
    "Stealth aircraft: matrix nearly empty — no 90° dihedrals → double-bounce suppressed.",
    ha='center', color=DIM, fontsize=9, wrap=True)

plt.tight_layout()
fig14.savefig(f'{OUT}/fig14_double_bounce_map.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig14)
print("  → fig14_double_bounce_map.png")

print("\n✓  All figures written to", OUT)
print("\n── PHYSICS UPGRADE SUMMARY ─────────────────────────────────────────")
print("  PTD edges found:")
print(f"    Conventional : {len(ptd_c.edges)} edges  "
      f"({sum(1 for _,_,a in ptd_c.edges if len(a)==1)} boundary, "
      f"{sum(1 for _,_,a in ptd_c.edges if len(a)==2)} internal)")
print(f"    Stealth      : {len(ptd_s.edges)} edges  "
      f"({sum(1 for _,_,a in ptd_s.edges if len(a)==1)} boundary, "
      f"{sum(1 for _,_,a in ptd_s.edges if len(a)==2)} internal)")
print(f"\n  Wedge parameters (n):")
print(f"    Conventional : min={ptd_c.edge_n.min():.2f}  "
      f"mean={ptd_c.edge_n.mean():.2f}  max={ptd_c.edge_n.max():.2f}")
print(f"    Stealth      : min={ptd_s.edge_n.min():.2f}  "
      f"mean={ptd_s.edge_n.mean():.2f}  max={ptd_s.edge_n.max():.2f}")
print("\n  (Higher mean n = more edge diffraction = more energy scattered)")
