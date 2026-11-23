"""
main.py
=======
Full RCS comparative analysis: Conventional vs Stealth geometry.

Generates 5 publication-quality figures:
  Fig 1 — 3D geometry views
  Fig 2 — Azimuth RCS polar patterns (X-band, 10 GHz)
  Fig 3 — Frequency sweep (L → Ka band) at nose-on and broadside
  Fig 4 — RCS heatmaps: azimuth × elevation
  Fig 5 — Summary statistics and reduction metrics
"""

import os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs
import matplotlib.ticker as mticker
from matplotlib.colors import Normalize, LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D                    # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/claude/rcs_project')
from geometries import conventional_aircraft, stealth_aircraft, sphere_mesh, flat_plate
from solvers    import PhysicalOpticsSolver, mie_rcs_dbsm, mie_frequency_sweep, frequency_sweep

OUT = './output'
os.makedirs(OUT, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────

BG       = '#080C14'
PANEL    = '#0E1420'
GRID_C   = '#1E2A3A'
TEXT     = '#D0DCF0'
DIM      = '#6A7A9A'

C_CONV   = '#FF5B35'   # orange-red   – conventional
C_STLTH  = '#00E5FF'   # electric cyan – stealth
C_SPHERE = '#FFD040'   # gold          – sphere
C_PLATE  = '#7CFC00'   # lime          – flat plate
C_ACCENT = '#C084FC'   # purple

RADAR_CMAP = LinearSegmentedColormap.from_list(
    'radar', ['#080C14', '#0A2040', '#004080', '#0080C0',
               '#00C0E0', '#40E080', '#C0E040', '#FFB000', '#FF4000'])

FREQ_GHZ = 10.0          # default X-band frequency
FREQ_HZ  = FREQ_GHZ * 1e9

print("Building geometries …")
V_CONV,  F_CONV  = conventional_aircraft()
V_STLTH, F_STLTH = stealth_aircraft()
V_SPH,   F_SPH   = sphere_mesh(radius=1.0)
V_PLATE, F_PLATE = flat_plate(2.0, 2.0)
print(f"  Conventional : {len(F_CONV):,} facets")
print(f"  Stealth      : {len(F_STLTH):,} facets")
print(f"  Sphere       : {len(F_SPH):,} facets")
print(f"  Flat Plate   : {len(F_PLATE):,} facets")

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def set_bg(fig, axes=None):
    fig.patch.set_facecolor(BG)
    if axes is not None:
        for ax in axes:
            ax.set_facecolor(PANEL)

def style_ax(ax, xlabel='', ylabel='', title=''):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=DIM, labelsize=8)
    ax.xaxis.label.set_color(DIM);  ax.xaxis.label.set_size(9)
    ax.yaxis.label.set_color(DIM);  ax.yaxis.label.set_size(9)
    ax.set_title(title, color=TEXT, fontsize=10, fontweight='bold', pad=6)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.grid(color=GRID_C, linewidth=0.6, linestyle='--', alpha=0.8)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_C)
    if xlabel: ax.set_xlabel(xlabel)
    if ylabel: ax.set_ylabel(ylabel)

def style_polar(ax, title='', r_min=-40, r_max=40):
    ax.set_facecolor(PANEL)
    ax.set_theta_zero_location('N')   # 0° at top
    ax.set_theta_direction(-1)        # clockwise (aviation convention)
    ax.set_ylim(r_min, r_max)
    ax.set_title(title, color=TEXT, fontsize=9, fontweight='bold', pad=10)
    ax.tick_params(colors=DIM, labelsize=7)
    ax.grid(color=GRID_C, linewidth=0.5, alpha=0.7)
    ax.spines['polar'].set_color(GRID_C)
    # Custom r-tick labels with units
    ticks = np.arange(r_min, r_max + 1, 10)
    ax.set_yticks(ticks)
    ax.set_yticklabels([f'{t}' for t in ticks], color=DIM, fontsize=6)
    # Azimuth labels
    ax.set_xticklabels(
        ['N\n0°', '45°', 'E\n90°', '135°', 'S\n180°', '225°', 'W\n270°', '315°'],
        fontsize=7, color=DIM)

def draw_geometry_3d(ax, vertices, faces, color, alpha=0.65, lw=0.15):
    tris = [vertices[f] for f in faces]
    poly = Poly3DCollection(tris, alpha=alpha, linewidth=lw,
                             facecolor=color, edgecolor='#2A3A50')
    ax.add_collection3d(poly)
    v = vertices
    margin = 0.3
    ax.set_xlim(v[:,0].min()-margin, v[:,0].max()+margin)
    ax.set_ylim(v[:,1].min()-margin, v[:,1].max()+margin)
    ax.set_zlim(v[:,2].min()-margin, v[:,2].max()+margin)
    ax.set_facecolor(BG)
    for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
        pane.fill = False; pane.set_edgecolor('#1A2434')
    for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
        axis.label.set_color(DIM); axis.label.set_size(7)
    ax.tick_params(colors='#3A4A60', labelsize=6)
    ax.set_xlabel('X (m)', labelpad=2)
    ax.set_ylabel('Y (m)', labelpad=2)
    ax.set_zlabel('Z (m)', labelpad=2)


# ═════════════════════════════════════════════════════════════════════════════
# FIG 1 — 3D GEOMETRY VIEWS
# ═════════════════════════════════════════════════════════════════════════════

print("\nFig 1: 3D geometry views …")

fig1 = plt.figure(figsize=(18, 9), facecolor=BG)
fig1.suptitle("RCS ANALYSIS  |  Geometry Comparison: Conventional vs Stealth",
               color=TEXT, fontsize=15, fontweight='bold', y=0.97)

angles_3d = [(25, -145), (20, -60), (30, -110)]  # (elev, azim) for each view
titles_3d  = ["Perspective View", "Front Quarter View", "Top View"]

for col, (elev, azim) in enumerate(angles_3d):
    # Conventional
    ax = fig1.add_subplot(2, 3, col+1, projection='3d')
    draw_geometry_3d(ax, V_CONV, F_CONV, C_CONV)
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(f"Conventional Aircraft — {titles_3d[col]}",
                  color=C_CONV, fontsize=9, fontweight='bold', pad=4)

    # Stealth
    ax = fig1.add_subplot(2, 3, col+4, projection='3d')
    draw_geometry_3d(ax, V_STLTH, F_STLTH, C_STLTH)
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(f"Stealth Aircraft — {titles_3d[col]}",
                  color=C_STLTH, fontsize=9, fontweight='bold', pad=4)

# Legend annotation
fig1.text(0.01, 0.50,
    "CONVENTIONAL\n"
    "┌ Box fuselage (flat sides)\n"
    "├ Flat 0° dihedral wings\n"
    "├ Vertical stabilizer (90°)\n"
    "└ Flat nose / intake face",
    color=C_CONV, fontsize=8, va='center', family='monospace',
    bbox=dict(facecolor='#1A0808', edgecolor=C_CONV, pad=6, alpha=0.7))

fig1.text(0.73, 0.50,
    "STEALTH\n"
    "┌ Faceted / trapezoidal fuselage\n"
    "├ Delta wings (65° LE sweep)\n"
    "├ V-tail canted 35° outward\n"
    "└ Pointed nose (tiny frontal area)",
    color=C_STLTH, fontsize=8, va='center', family='monospace',
    bbox=dict(facecolor='#001A1A', edgecolor=C_STLTH, pad=6, alpha=0.7))

plt.tight_layout(rect=[0, 0, 1, 0.95])
fig1.savefig(f'{OUT}/fig1_geometry_3d.png', dpi=150, bbox_inches='tight',
              facecolor=BG)
plt.close(fig1)
print("  → fig1_geometry_3d.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 2 — AZIMUTH RCS POLAR PATTERNS (X-band, 10 GHz)
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 2: Azimuth polar RCS patterns …")

N_AZ = 360
print("  Computing sphere (Mie) …")
sphere_rcs_const = mie_rcs_dbsm(1.0, FREQ_HZ)
sphere_rcs       = np.full(N_AZ, sphere_rcs_const)

print("  Computing flat plate …")
sol_plate = PhysicalOpticsSolver(V_PLATE, F_PLATE, FREQ_HZ)
az_angles, rcs_plate = sol_plate.azimuth_sweep(N_AZ)

print("  Computing conventional aircraft …")
sol_conv = PhysicalOpticsSolver(V_CONV, F_CONV, FREQ_HZ)
_,         rcs_conv  = sol_conv.azimuth_sweep(N_AZ)

print("  Computing stealth aircraft …")
sol_stlth = PhysicalOpticsSolver(V_STLTH, F_STLTH, FREQ_HZ)
_,          rcs_stlth = sol_stlth.azimuth_sweep(N_AZ)

az_rad = np.radians(az_angles)

fig2 = plt.figure(figsize=(20, 10), facecolor=BG)
fig2.suptitle(f"Azimuth RCS Patterns  |  X-band {FREQ_GHZ:.0f} GHz  |  Horizontal Polarisation  |  El = 0°",
               color=TEXT, fontsize=14, fontweight='bold', y=0.98)

datasets = [
    ("Sphere (r=1 m)\nMie Series [exact]",  sphere_rcs, C_SPHERE, az_rad),
    ("Flat Plate (2×2 m)\nPhysical Optics",  rcs_plate,  C_PLATE,  az_rad),
    ("Conventional Aircraft\nPhysical Optics", rcs_conv,  C_CONV,   az_rad),
    ("Stealth Aircraft\nPhysical Optics",    rcs_stlth,  C_STLTH,  az_rad),
]

r_global_min = min(d[1].min() for d in datasets) - 3
r_global_max = max(d[1].max() for d in datasets) + 3

for idx, (title, rcs, color, ang) in enumerate(datasets):
    ax = fig2.add_subplot(2, 4, idx+1, projection='polar')
    style_polar(ax, title, r_min=r_global_min, r_max=r_global_max)
    ax.plot(ang, rcs, color=color, lw=1.4, alpha=0.95)
    ax.fill(ang, rcs, color=color, alpha=0.15)
    # Mark peak
    peak_idx = np.argmax(rcs)
    ax.plot(ang[peak_idx], rcs[peak_idx], 'o', color='white', ms=5, zorder=5)
    ax.annotate(f'{rcs[peak_idx]:.1f} dBsm',
                xy=(ang[peak_idx], rcs[peak_idx]),
                xytext=(ang[peak_idx] + 0.3, rcs[peak_idx] + 4),
                color='white', fontsize=6, fontweight='bold')

# Overlaid comparison plot (right side)
ax_ov = fig2.add_subplot(1, 2, 2, projection='polar')
style_polar(ax_ov, "All Geometries — Overlaid\n(same scale)",
             r_min=r_global_min, r_max=r_global_max)
for title, rcs, color, ang in datasets:
    label = title.split('\n')[0]
    ax_ov.plot(ang, rcs, color=color, lw=1.6, alpha=0.90, label=label)
    ax_ov.fill(ang, rcs, color=color, alpha=0.08)
ax_ov.legend(loc='lower right', bbox_to_anchor=(1.35, -0.05),
              fontsize=8, labelcolor=TEXT,
              facecolor='#0E1420', edgecolor=GRID_C, framealpha=0.8)

plt.tight_layout(rect=[0, 0, 1, 0.95])
fig2.savefig(f'{OUT}/fig2_polar_rcs.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig2)
print("  → fig2_polar_rcs.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 3 — FREQUENCY SWEEP  (L-band → Ka-band, 1 – 36 GHz)
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 3: Frequency sweep …")

FREQS = np.linspace(1e9, 36e9, 120)  # 1 – 36 GHz
FREQS_GHZ = FREQS / 1e9

print("  Sphere (Mie) …")
rcs_sph_freq = mie_frequency_sweep(1.0, FREQS)

print("  Conventional @ 0° …");  rcs_conv_0   = frequency_sweep(V_CONV,  F_CONV,  FREQS, 0.0)
print("  Conventional @ 90°…");  rcs_conv_90  = frequency_sweep(V_CONV,  F_CONV,  FREQS, 90.0)
print("  Stealth @ 0° …");       rcs_stlth_0  = frequency_sweep(V_STLTH, F_STLTH, FREQS, 0.0)
print("  Stealth @ 90°…");       rcs_stlth_90 = frequency_sweep(V_STLTH, F_STLTH, FREQS, 90.0)

fig3, axes = plt.subplots(1, 3, figsize=(20, 6), facecolor=BG)
set_bg(fig3, axes)
fig3.suptitle("RCS vs Radar Frequency  |  L-band → Ka-band  (1 – 36 GHz)",
               color=TEXT, fontsize=14, fontweight='bold', y=1.01)

band_spans = [  # (fmin GHz, fmax GHz, label, color)
    (1,  2,  'L',  '#223344'), (2,  4,  'S',  '#1A2E44'),
    (4,  8,  'C',  '#223344'), (8,  12, 'X',  '#1A2E44'),
    (12, 18, 'Ku', '#223344'), (18, 27, 'Ka', '#1A2E44'),
]

def add_band_shading(ax):
    ylim = ax.get_ylim()
    for f0, f1, lbl, c in band_spans:
        if f1 <= FREQS_GHZ[-1]:
            ax.axvspan(f0, f1, color=c, alpha=0.4, zorder=0)
            ax.text((f0+f1)/2, ylim[0] + 0.5, lbl,
                     color='#4A6080', fontsize=7, ha='center', va='bottom')

# --- Subplot 1: nose-on (0°) ---
ax = axes[0]
style_ax(ax, 'Frequency (GHz)', 'RCS (dBsm)', 'Nose-on  (0°)  —  Frontal Threat')
ax.plot(FREQS_GHZ, rcs_conv_0,   color=C_CONV,   lw=2.0, label='Conventional')
ax.plot(FREQS_GHZ, rcs_stlth_0,  color=C_STLTH,  lw=2.0, label='Stealth')
ax.fill_between(FREQS_GHZ, rcs_conv_0, rcs_stlth_0,
                 where=rcs_conv_0 > rcs_stlth_0,
                 color='#00CC44', alpha=0.12, label='RCS reduction zone')
ax.set_xlim(1, 36); add_band_shading(ax)
ax.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)
ax.axvline(10, color='#FF8C00', lw=1, ls=':', alpha=0.7)
ax.text(10.2, ax.get_ylim()[1]*0.97, 'X-band\n10 GHz', color='#FF8C00', fontsize=7)

# --- Subplot 2: broadside (90°) ---
ax = axes[1]
style_ax(ax, 'Frequency (GHz)', 'RCS (dBsm)', 'Broadside  (90°)  —  Side Threat')
ax.plot(FREQS_GHZ, rcs_conv_90,  color=C_CONV,   lw=2.0, label='Conventional')
ax.plot(FREQS_GHZ, rcs_stlth_90, color=C_STLTH,  lw=2.0, label='Stealth')
ax.fill_between(FREQS_GHZ, rcs_conv_90, rcs_stlth_90,
                 where=rcs_conv_90 > rcs_stlth_90,
                 color='#00CC44', alpha=0.12)
ax.set_xlim(1, 36); add_band_shading(ax)
ax.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)
ax.axvline(10, color='#FF8C00', lw=1, ls=':', alpha=0.7)

# --- Subplot 3: Mie validation + reduction dB ---
ax = axes[2]
style_ax(ax, 'Frequency (GHz)', 'RCS Reduction  ΔdBsm', 'RCS Reduction  (Conventional − Stealth)')
delta_0  = rcs_conv_0  - rcs_stlth_0
delta_90 = rcs_conv_90 - rcs_stlth_90
ax.plot(FREQS_GHZ, delta_0,  color=C_SPHERE, lw=2.0, label='ΔσNose-on (0°)')
ax.plot(FREQS_GHZ, delta_90, color=C_PLATE,  lw=2.0, label='ΔσBroadside (90°)')
ax.fill_between(FREQS_GHZ, delta_0,  0, where=delta_0  > 0, color=C_SPHERE, alpha=0.12)
ax.fill_between(FREQS_GHZ, delta_90, 0, where=delta_90 > 0, color=C_PLATE,  alpha=0.12)
ax.axhline(0, color=DIM, lw=0.8, ls='--')
ax.set_xlim(1, 36); add_band_shading(ax)
ax.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)

plt.tight_layout()
fig3.savefig(f'{OUT}/fig3_frequency_sweep.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig3)
print("  → fig3_frequency_sweep.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 4 — RCS HEATMAPS  (azimuth × elevation)
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 4: RCS heatmaps (az × el) …")

N_AZ_HM, N_EL_HM = 120, 60
print("  Conventional heatmap …")
sol_c = PhysicalOpticsSolver(V_CONV, F_CONV, FREQ_HZ)
azs_hm, els_hm, grid_conv  = sol_c.heatmap(N_AZ_HM, N_EL_HM)

print("  Stealth heatmap …")
sol_s = PhysicalOpticsSolver(V_STLTH, F_STLTH, FREQ_HZ)
_,     _,       grid_stlth = sol_s.heatmap(N_AZ_HM, N_EL_HM)

vmin = min(grid_conv.min(), grid_stlth.min())
vmax = max(grid_conv.max(), grid_stlth.max())

fig4, axes = plt.subplots(1, 3, figsize=(21, 7), facecolor=BG,
                            gridspec_kw={'width_ratios': [1, 1, 0.04]})
set_bg(fig4, axes[:2])
fig4.suptitle(f"Full-Sphere RCS Heatmap  |  {FREQ_GHZ:.0f} GHz X-band  |  Azimuth × Elevation",
               color=TEXT, fontsize=13, fontweight='bold', y=1.01)

extent = [azs_hm[0], azs_hm[-1], els_hm[0], els_hm[-1]]

im_c = axes[0].imshow(grid_conv,  aspect='auto', extent=extent,
                       origin='lower', cmap=RADAR_CMAP, vmin=vmin, vmax=vmax)
style_ax(axes[0], 'Azimuth (°)', 'Elevation (°)', 'Conventional Aircraft')
axes[0].set_title('CONVENTIONAL AIRCRAFT', color=C_CONV,   fontsize=11, fontweight='bold')

im_s = axes[1].imshow(grid_stlth, aspect='auto', extent=extent,
                       origin='lower', cmap=RADAR_CMAP, vmin=vmin, vmax=vmax)
style_ax(axes[1], 'Azimuth (°)', 'Elevation (°)', '')
axes[1].set_title('STEALTH AIRCRAFT',       color=C_STLTH,  fontsize=11, fontweight='bold')

# Shared colorbar
cb = plt.colorbar(im_s, cax=axes[2])
cb.set_label('RCS  (dBsm)', color=TEXT, fontsize=9)
cb.ax.yaxis.set_tick_params(color=DIM, labelcolor=DIM)

# Annotate key angles on conventional
for az_ann, el_ann, note in [(90, 0, 'Broadside\nspike'), (0, 0, 'Nose-on'), (180, 0, 'Tail-on')]:
    axes[0].plot(az_ann, el_ann, 'w+', ms=10, mew=1.5)
    axes[0].text(az_ann+2, el_ann+3, note, color='white', fontsize=7, alpha=0.8)

for ax in axes[:2]:
    ax.axvline(0,   color='#FF8C00', lw=0.8, ls='--', alpha=0.5)
    ax.axvline(90,  color='#FF8C00', lw=0.8, ls='--', alpha=0.5)
    ax.axvline(180, color='#FF8C00', lw=0.8, ls='--', alpha=0.5)
    ax.axvline(270, color='#FF8C00', lw=0.8, ls='--', alpha=0.5)

plt.tight_layout()
fig4.savefig(f'{OUT}/fig4_heatmaps.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig4)
print("  → fig4_heatmaps.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 5 — SUMMARY STATISTICS & DESIGN PRINCIPLES
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 5: Summary statistics …")

def rcs_stats(rcs_arr):
    return {
        'peak':   rcs_arr.max(),
        'mean':   rcs_arr.mean(),
        'median': float(np.median(rcs_arr)),
        'p90':    float(np.percentile(rcs_arr, 90)),
    }

stats_conv  = rcs_stats(rcs_conv)
stats_stlth = rcs_stats(rcs_stlth)
stats_sph   = rcs_stats(sphere_rcs)
stats_plate = rcs_stats(rcs_plate)

fig5 = plt.figure(figsize=(20, 10), facecolor=BG)
fig5.suptitle("RCS Comparative Analysis — Summary & Design Principles",
               color=TEXT, fontsize=14, fontweight='bold', y=0.98)

grid5 = gs.GridSpec(2, 3, figure=fig5, hspace=0.45, wspace=0.35,
                    left=0.06, right=0.97, top=0.92, bottom=0.07)

# ── Bar chart: peak & mean RCS ──
ax_bar = fig5.add_subplot(grid5[0, 0])
style_ax(ax_bar, '', 'RCS (dBsm)', 'Peak & Mean RCS Comparison')

labels   = ['Sphere', 'Flat\nPlate', 'Conventional', 'Stealth']
peaks    = [stats_sph['peak'], stats_plate['peak'],
             stats_conv['peak'],  stats_stlth['peak']]
means    = [stats_sph['mean'], stats_plate['mean'],
             stats_conv['mean'],  stats_stlth['mean']]
colors   = [C_SPHERE, C_PLATE, C_CONV, C_STLTH]

x = np.arange(len(labels))
w = 0.35
bars1 = ax_bar.bar(x - w/2, peaks, w, color=colors, alpha=0.85, label='Peak RCS')
bars2 = ax_bar.bar(x + w/2, means, w, color=colors, alpha=0.45,
                    edgecolor=colors, linewidth=1.2, label='Mean RCS')
for bar in bars1:
    ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 f'{bar.get_height():.1f}', ha='center', va='bottom',
                 color=TEXT, fontsize=7, fontweight='bold')
ax_bar.set_xticks(x); ax_bar.set_xticklabels(labels, color=TEXT, fontsize=8)
ax_bar.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)

# ── Reduction bar chart ──
ax_red = fig5.add_subplot(grid5[0, 1])
style_ax(ax_red, 'Look Angle', 'Reduction  ΔdBsm', 'RCS Reduction  (Conv − Stealth)')

angle_labels = ['Nose-on\n0°', 'Broadside\n90°', 'Tail-on\n180°']
delta_vals   = [
    sol_conv.monostatic_rcs_dbsm(0)   - sol_stlth.monostatic_rcs_dbsm(0),
    sol_conv.monostatic_rcs_dbsm(90)  - sol_stlth.monostatic_rcs_dbsm(90),
    sol_conv.monostatic_rcs_dbsm(180) - sol_stlth.monostatic_rcs_dbsm(180),
]
bar_colors = ['#00CC44' if d > 0 else '#FF4444' for d in delta_vals]
bars = ax_red.bar(angle_labels, delta_vals, color=bar_colors, alpha=0.85, width=0.5)
for bar, val in zip(bars, delta_vals):
    ax_red.text(bar.get_x() + bar.get_width()/2,
                 max(val, 0) + 0.2,
                 f'{val:+.1f} dB', ha='center', va='bottom',
                 color=TEXT, fontsize=9, fontweight='bold')
ax_red.axhline(0, color=DIM, lw=1, ls='--')
ax_red.set_xticklabels(angle_labels, color=TEXT, fontsize=9)

# ── RCS linear scale comparison (magnitude, not log) ──
ax_lin = fig5.add_subplot(grid5[0, 2])
style_ax(ax_lin, 'Azimuth (°)', 'σ (m²)  [linear]', 'Linear RCS vs Azimuth  (0–90°)')
az_short = az_angles[:N_AZ//4]
rcs_conv_lin  = 10**(rcs_conv[:N_AZ//4]  / 10)
rcs_stlth_lin = 10**(rcs_stlth[:N_AZ//4] / 10)
ax_lin.semilogy(az_short, rcs_conv_lin,  color=C_CONV,  lw=2, label='Conventional')
ax_lin.semilogy(az_short, rcs_stlth_lin, color=C_STLTH, lw=2, label='Stealth')
ax_lin.fill_between(az_short, rcs_conv_lin, rcs_stlth_lin,
                     where=rcs_conv_lin > rcs_stlth_lin,
                     color='#00CC44', alpha=0.15)
ax_lin.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)
ax_lin.set_xlim(0, 90)
ax_lin.yaxis.set_tick_params(labelcolor=DIM, labelsize=7)

# ── Key design principles text panel ──
ax_txt = fig5.add_subplot(grid5[1, :])
ax_txt.set_facecolor(PANEL)
ax_txt.axis('off')
for spine in ax_txt.spines.values(): spine.set_edgecolor(GRID_C)

principles = [
    ("Geometric Shaping",
     "All surfaces inclined ≥15° from perpendicular to threat axis. "
     "Eliminates specular returns toward nose-on (0°) direction."),
    ("Leading-Edge Alignment",
     "Wing leading edges aligned to concentrate spikes into narrow angular sectors. "
     "Redirects energy to non-threat aspects (typically ~65° off nose)."),
    ("V-Tail Cant Angle",
     "Vertical stabilizer replaced by canted V-tails (35°). "
     "Eliminates 90° dihedral corner reflector with fuselage — removes dominant broadside spike."),
    ("Fuselage Cross-Section",
     "Trapezoidal/diamond cross-section replaces rectangular box. "
     "Angled side walls scatter energy above/below rather than back to radar."),
    ("Edge Treatments",
     "Parallel edge alignment (all trailing edges parallel) reduces diffraction lobes. "
     "Sawtooth patterns produce controlled scattering at designed frequencies."),
    ("Material Integration",
     "Geometry shaping provides ~15–25 dB RCS reduction. "
     "RAM coatings add further 10–20 dB, especially at nose-on aspect."),
]

n_col = 3
col_w = 1.0 / n_col
for i, (title, body) in enumerate(principles):
    col = i % n_col
    row = i // n_col
    x = 0.01 + col * col_w
    y = 0.90 - row * 0.48
    ax_txt.text(x, y, f"▶  {title}", color=C_ACCENT, fontsize=9,
                 fontweight='bold', transform=ax_txt.transAxes)
    ax_txt.text(x, y - 0.12, body, color=TEXT, fontsize=7.5,
                 transform=ax_txt.transAxes, wrap=True,
                 verticalalignment='top',
                 bbox=dict(facecolor='#0A0E1A', alpha=0.0))

ax_txt.set_title("LOW-OBSERVABLE DESIGN PRINCIPLES",
                  color=TEXT, fontsize=11, fontweight='bold', pad=8)
ax_txt.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax_txt.transAxes,
                                 facecolor='none', edgecolor=GRID_C, linewidth=1))

fig5.savefig(f'{OUT}/fig5_summary.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig5)
print("  → fig5_summary.png")


# ═════════════════════════════════════════════════════════════════════════════
# DONE
# ═════════════════════════════════════════════════════════════════════════════

print("\n✓ All figures saved to", OUT)
print("\n── NUMERICAL SUMMARY ─────────────────────────────────────────────")
print(f"{'Geometry':<25}  {'Peak (dBsm)':>12}  {'Mean (dBsm)':>12}  {'Median (dBsm)':>14}")
print("─" * 70)
for name, st in [("Sphere (Mie)", stats_sph), ("Flat Plate", stats_plate),
                  ("Conventional A/C", stats_conv), ("Stealth A/C", stats_stlth)]:
    print(f"  {name:<23}  {st['peak']:>12.1f}  {st['mean']:>12.1f}  {st['median']:>14.1f}")
print("─" * 70)
print(f"\n  RCS Reduction (Conv→Stealth):")
print(f"    Nose-on  (0°)  : {delta_vals[0]:+.1f} dB")
print(f"    Broadside (90°): {delta_vals[1]:+.1f} dB")
print(f"    Tail-on  (180°): {delta_vals[2]:+.1f} dB")
