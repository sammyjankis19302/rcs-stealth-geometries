"""
main2.py
========
Extended RCS analysis (Part 2):

  Fig 6  — All 6 geometries: 3D views (Sphere, Plate, Conventional,
           Stealth, Flying Wing, Chined-Nose)
  Fig 7  — RAM coating effect: RCS vs frequency, bare vs coated
  Fig 8  — Bistatic RCS patterns (forward-scatter behaviour)
  Fig 9  — All-geometry azimuth comparison overlay + ranking table
  Anim 1 — Rotating 3D view + live RCS polar plot (GIF)
"""

import os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D                    # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import imageio.v2 as imageio
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/claude/rcs_project')
from geometries import (conventional_aircraft, stealth_aircraft, sphere_mesh,
                         flat_plate, flying_wing, chined_nose_aircraft)
from solvers import (PhysicalOpticsSolver, mie_rcs_dbsm, mie_frequency_sweep,
                      frequency_sweep, bistatic_sweep)

OUT = './outputs'
os.makedirs(OUT, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS  (kept consistent with main.py)
# ─────────────────────────────────────────────────────────────────────────────

BG       = '#080C14'
PANEL    = '#0E1420'
GRID_C   = '#1E2A3A'
TEXT     = '#D0DCF0'
DIM      = '#6A7A9A'

C_CONV   = '#FF5B35'
C_STLTH  = '#00E5FF'
C_SPHERE = '#FFD040'
C_PLATE  = '#7CFC00'
C_ACCENT = '#C084FC'
C_WING   = '#FF6EC7'   # flying wing  - pink
C_CHINE  = '#39FF88'   # chined nose  - mint green

RADAR_CMAP = LinearSegmentedColormap.from_list(
    'radar', ['#080C14', '#0A2040', '#004080', '#0080C0',
               '#00C0E0', '#40E080', '#C0E040', '#FFB000', '#FF4000'])

FREQ_GHZ = 10.0
FREQ_HZ  = FREQ_GHZ * 1e9

print("Building geometries …")
V_CONV,  F_CONV  = conventional_aircraft()
V_STLTH, F_STLTH = stealth_aircraft()
V_SPH,   F_SPH   = sphere_mesh(radius=1.0)
V_PLATE, F_PLATE = flat_plate(2.0, 2.0)
V_WING,  F_WING  = flying_wing()
V_CHINE, F_CHINE = chined_nose_aircraft()
print(f"  Conventional : {len(F_CONV):,} facets")
print(f"  Stealth      : {len(F_STLTH):,} facets")
print(f"  Flying Wing  : {len(F_WING):,} facets")
print(f"  Chined Nose  : {len(F_CHINE):,} facets")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS  (mirrors main.py)
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

def style_polar(ax, title='', r_min=-40, r_max=40):
    ax.set_facecolor(PANEL)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_ylim(r_min, r_max)
    ax.set_title(title, color=TEXT, fontsize=9, fontweight='bold', pad=10)
    ax.tick_params(colors=DIM, labelsize=7)
    ax.grid(color=GRID_C, linewidth=0.5, alpha=0.7)
    ax.spines['polar'].set_color(GRID_C)
    ticks = np.arange(r_min, r_max + 1, 10)
    ax.set_yticks(ticks)
    ax.set_yticklabels([f'{t}' for t in ticks], color=DIM, fontsize=6)
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


# ═════════════════════════════════════════════════════════════════════════════
# FIG 6 — ALL 6 GEOMETRIES, 3D VIEWS
# ═════════════════════════════════════════════════════════════════════════════

print("\nFig 6: All geometries 3D views …")

fig6 = plt.figure(figsize=(18, 11), facecolor=BG)
fig6.suptitle("Extended Geometry Set  |  6 Configurations",
               color=TEXT, fontsize=15, fontweight='bold', y=0.98)

geoms6 = [
    ("Sphere",          V_SPH,   F_SPH,   C_SPHERE, (20, -60)),
    ("Flat Plate",      V_PLATE, F_PLATE, C_PLATE,  (20, -60)),
    ("Conventional A/C",V_CONV,  F_CONV,  C_CONV,   (25, -145)),
    ("Stealth A/C",     V_STLTH, F_STLTH, C_STLTH,  (25, -145)),
    ("Flying Wing\n(B-2 style)",   V_WING,  F_WING,  C_WING,  (35, -145)),
    ("Chined Nose\n(F-22 style)",  V_CHINE, F_CHINE, C_CHINE, (25, -145)),
]

for idx, (name, V, F, color, view) in enumerate(geoms6):
    ax = fig6.add_subplot(2, 3, idx+1, projection='3d')
    draw_geometry_3d(ax, V, F, color)
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_title(name, color=color, fontsize=11, fontweight='bold', pad=6)

plt.tight_layout(rect=[0, 0, 1, 0.95])
fig6.savefig(f'{OUT}/fig6_all_geometries.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig6)
print("  → fig6_all_geometries.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 7 — RAM COATING EFFECT
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 7: RAM coating effect …")

FREQS = np.linspace(1e9, 36e9, 100)
FREQS_GHZ = FREQS / 1e9

RAM_LEVELS = [None, 5, 10, 20]  # dB one-way absorption
RAM_LABELS = ['Bare metal', 'RAM 5 dB', 'RAM 10 dB', 'RAM 20 dB']
RAM_COLORS = ['#FF5B35', '#FFA040', '#7CFC00', '#00E5FF']

print("  Stealth aircraft, nose-on, varying RAM …")
rcs_ram_stealth = {}
for lvl, lbl in zip(RAM_LEVELS, RAM_LABELS):
    rcs_ram_stealth[lbl] = frequency_sweep(V_STLTH, F_STLTH, FREQS, 0.0, 0.0, ram_db=lvl)

print("  Conventional aircraft, nose-on, varying RAM …")
rcs_ram_conv = {}
for lvl, lbl in zip(RAM_LEVELS, RAM_LABELS):
    rcs_ram_conv[lbl] = frequency_sweep(V_CONV, F_CONV, FREQS, 0.0, 0.0, ram_db=lvl)

fig7, axes = plt.subplots(1, 3, figsize=(20, 6), facecolor=BG)
set_bg(fig7, axes)
fig7.suptitle("Radar Absorbing Material (RAM) Coating Effect  |  Nose-on (0°)",
               color=TEXT, fontsize=14, fontweight='bold', y=1.02)

# --- Subplot 1: Stealth + RAM ---
ax = axes[0]
style_ax(ax, 'Frequency (GHz)', 'RCS (dBsm)', 'Stealth Airframe + RAM')
for lbl, color in zip(RAM_LABELS, RAM_COLORS):
    ax.plot(FREQS_GHZ, rcs_ram_stealth[lbl], color=color, lw=2.0, label=lbl)
ax.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)
ax.set_xlim(1, 36)

# --- Subplot 2: Conventional + RAM ---
ax = axes[1]
style_ax(ax, 'Frequency (GHz)', 'RCS (dBsm)', 'Conventional Airframe + RAM')
for lbl, color in zip(RAM_LABELS, RAM_COLORS):
    ax.plot(FREQS_GHZ, rcs_ram_conv[lbl], color=color, lw=2.0, label=lbl)
ax.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)
ax.set_xlim(1, 36)

# --- Subplot 3: Combined reduction stack at X-band ---
ax = axes[2]
style_ax(ax, '', 'RCS (dBsm)', 'X-band (10 GHz) Reduction Stack')
idx10 = np.argmin(np.abs(FREQS_GHZ - 10))

bare_conv   = rcs_ram_conv['Bare metal'][idx10]
shape_only  = rcs_ram_stealth['Bare metal'][idx10]
shape_ram5  = rcs_ram_stealth['RAM 5 dB'][idx10]
shape_ram10 = rcs_ram_stealth['RAM 10 dB'][idx10]
shape_ram20 = rcs_ram_stealth['RAM 20 dB'][idx10]

stack_labels = ['Conventional\n(baseline)', 'Stealth\nshape only',
                'Shape\n+ RAM 5dB', 'Shape\n+ RAM 10dB', 'Shape\n+ RAM 20dB']
stack_vals   = [bare_conv, shape_only, shape_ram5, shape_ram10, shape_ram20]
stack_colors = [C_CONV, C_STLTH, '#FFA040', '#7CFC00', '#00E5FF']

bars = ax.bar(stack_labels, stack_vals, color=stack_colors, alpha=0.85, width=0.6)
for bar, val in zip(bars, stack_vals):
    ax.text(bar.get_x() + bar.get_width()/2, val + (1.5 if val > 0 else -3.5),
            f'{val:.1f}', ha='center', color=TEXT, fontsize=9, fontweight='bold')
ax.axhline(bare_conv, color=C_CONV, lw=1, ls=':', alpha=0.6)
for label in ax.get_xticklabels():
    label.set_fontsize(8); label.set_color(TEXT)
ax.text(4.3, bare_conv + 1.5, f'Total reduction:\n{bare_conv - shape_ram20:.1f} dB',
        color='#00E5FF', fontsize=9, fontweight='bold', ha='right')

plt.tight_layout()
fig7.savefig(f'{OUT}/fig7_ram_coating.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig7)
print("  → fig7_ram_coating.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 8 — BISTATIC RCS PATTERNS
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 8: Bistatic RCS patterns …")

print("  Conventional, Tx @ 0° …")
bi_angles, bi_conv_0 = bistatic_sweep(V_CONV, F_CONV, FREQ_HZ, az_tx_deg=0.0)
print("  Stealth, Tx @ 0° …")
_,         bi_stlth_0 = bistatic_sweep(V_STLTH, F_STLTH, FREQ_HZ, az_tx_deg=0.0)
print("  Conventional, Tx @ 45° …")
_,         bi_conv_45 = bistatic_sweep(V_CONV, F_CONV, FREQ_HZ, az_tx_deg=45.0)
print("  Stealth, Tx @ 45° …")
_,         bi_stlth_45 = bistatic_sweep(V_STLTH, F_STLTH, FREQ_HZ, az_tx_deg=45.0)

fig8, axes = plt.subplots(1, 2, figsize=(16, 7), facecolor=BG)
set_bg(fig8, axes)
fig8.suptitle(f"Bistatic RCS  |  {FREQ_GHZ:.0f} GHz  |  Bistatic Angle β = Rx offset from Tx",
               color=TEXT, fontsize=14, fontweight='bold', y=1.02)

ax = axes[0]
style_ax(ax, 'Bistatic angle β (°)', 'RCS (dBsm)', 'Illumination from Nose-on (Tx @ 0°)')
ax.plot(bi_angles, bi_conv_0,  color=C_CONV,  lw=2, label='Conventional')
ax.plot(bi_angles, bi_stlth_0, color=C_STLTH, lw=2, label='Stealth')
ax.axvline(0, color=DIM, lw=1, ls=':', label='Monostatic (β=0)')
ax.axvline(180, color='#FFA040', lw=1, ls='--', alpha=0.6)
ax.axvline(-180, color='#FFA040', lw=1, ls='--', alpha=0.6)
ax.text(178, ax.get_ylim()[1]-2, 'Forward\nscatter', color='#FFA040', fontsize=8, ha='right')
ax.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)

ax = axes[1]
style_ax(ax, 'Bistatic angle β (°)', 'RCS (dBsm)', 'Illumination from Quarter-on (Tx @ 45°)')
ax.plot(bi_angles, bi_conv_45,  color=C_CONV,  lw=2, label='Conventional')
ax.plot(bi_angles, bi_stlth_45, color=C_STLTH, lw=2, label='Stealth')
ax.axvline(0, color=DIM, lw=1, ls=':', label='Monostatic (β=0)')
ax.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)

plt.tight_layout()
fig8.savefig(f'{OUT}/fig8_bistatic.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig8)
print("  → fig8_bistatic.png")


# ═════════════════════════════════════════════════════════════════════════════
# FIG 9 — ALL-GEOMETRY OVERLAY + RANKING TABLE
# ═════════════════════════════════════════════════════════════════════════════

print("Fig 9: All-geometry comparison …")

N_AZ = 360
geoms_for_compare = [
    ("Sphere",           V_SPH,   F_SPH,   C_SPHERE),
    ("Flat Plate",       V_PLATE, F_PLATE, C_PLATE),
    ("Conventional A/C", V_CONV,  F_CONV,  C_CONV),
    ("Stealth A/C",      V_STLTH, F_STLTH, C_STLTH),
    ("Flying Wing",      V_WING,  F_WING,  C_WING),
    ("Chined Nose",      V_CHINE, F_CHINE, C_CHINE),
]

all_rcs = {}
for name, V, F, color in geoms_for_compare:
    if name == "Sphere":
        all_rcs[name] = np.full(N_AZ, mie_rcs_dbsm(1.0, FREQ_HZ))
        continue
    print(f"  {name} …")
    s = PhysicalOpticsSolver(V, F, FREQ_HZ)
    _, rcs = s.azimuth_sweep(N_AZ)
    all_rcs[name] = rcs

az_angles = np.linspace(0, 360, N_AZ, endpoint=False)
az_rad = np.radians(az_angles)

fig9 = plt.figure(figsize=(18, 8), facecolor=BG)
fig9.suptitle(f"All-Geometry Comparison  |  X-band {FREQ_GHZ:.0f} GHz  |  Azimuth Sweep",
               color=TEXT, fontsize=14, fontweight='bold', y=0.98)

grid9 = gs.GridSpec(1, 2, figure=fig9, width_ratios=[1.1, 1], wspace=0.3,
                     left=0.04, right=0.97, top=0.88, bottom=0.08)

ax_polar = fig9.add_subplot(grid9[0, 0], projection='polar')
r_min = min(r.min() for r in all_rcs.values()) - 3
r_max = max(r.max() for r in all_rcs.values()) + 3
style_polar(ax_polar, "All Geometries — Azimuth RCS", r_min=r_min, r_max=r_max)
for name, V, F, color in geoms_for_compare:
    ax_polar.plot(az_rad, all_rcs[name], color=color, lw=1.6, label=name, alpha=0.9)
ax_polar.legend(loc='upper right', bbox_to_anchor=(1.45, 1.1),
                 fontsize=8, labelcolor=TEXT, facecolor=PANEL, edgecolor=GRID_C)

# Ranking table panel
ax_tab = fig9.add_subplot(grid9[0, 1])
ax_tab.axis('off')
ax_tab.set_facecolor(PANEL)

rows = []
for name, V, F, color in geoms_for_compare:
    r = all_rcs[name]
    rows.append((name, r.max(), r.mean(), np.median(r), color))
rows_sorted = sorted(rows, key=lambda x: x[2])  # sort by mean RCS, lowest first

col_x = [0.02, 0.40, 0.62, 0.84]
headers = ['Geometry', 'Peak (dBsm)', 'Mean (dBsm)', 'Median']
y0 = 0.92
ax_tab.set_title("Stealth Ranking  (sorted by Mean RCS, lowest = stealthiest)",
                  color=TEXT, fontsize=11, fontweight='bold', pad=14)
for cx, h in zip(col_x, headers):
    ax_tab.text(cx, y0, h, color=DIM, fontsize=10, fontweight='bold',
                 transform=ax_tab.transAxes)
ax_tab.plot([0.0, 1.0], [y0-0.04, y0-0.04], color=GRID_C, lw=1,
             transform=ax_tab.transAxes)

row_h = 0.13
for i, (name, peak, mean, med, color) in enumerate(rows_sorted):
    y = y0 - 0.10 - i*row_h
    rank_badge = f"#{i+1}"
    ax_tab.add_patch(plt.Rectangle((0.0, y-0.045), 1.0, row_h-0.015,
                      transform=ax_tab.transAxes, facecolor=color, alpha=0.08))
    ax_tab.text(col_x[0]-0.0, y, f"{rank_badge}  {name}", color=color, fontsize=11,
                 fontweight='bold', transform=ax_tab.transAxes, va='center')
    ax_tab.text(col_x[1], y, f"{peak:.1f}", color=TEXT, fontsize=10,
                 transform=ax_tab.transAxes, va='center')
    ax_tab.text(col_x[2], y, f"{mean:.1f}", color=TEXT, fontsize=10,
                 transform=ax_tab.transAxes, va='center')
    ax_tab.text(col_x[3], y, f"{med:.1f}", color=TEXT, fontsize=10,
                 transform=ax_tab.transAxes, va='center')

ax_tab.text(0.0, y0 - 0.10 - len(rows_sorted)*row_h - 0.06,
             "Lower mean RCS → less average energy returned to a monostatic\n"
             "radar across all approach angles → harder to detect/track.",
             color=DIM, fontsize=9, transform=ax_tab.transAxes, va='top')

plt.tight_layout(rect=[0, 0, 1, 0.95])
fig9.savefig(f'{OUT}/fig9_all_geometry_comparison.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig9)
print("  → fig9_all_geometry_comparison.png")


# ═════════════════════════════════════════════════════════════════════════════
# ANIMATION 1 — ROTATING VIEW + LIVE RCS POLAR (GIF)
# ═════════════════════════════════════════════════════════════════════════════

print("Anim 1: Rotating view + live RCS (GIF) — this takes a minute …")

N_FRAMES = 60
sol_conv_anim  = PhysicalOpticsSolver(V_CONV,  F_CONV,  FREQ_HZ)
sol_stlth_anim = PhysicalOpticsSolver(V_STLTH, F_STLTH, FREQ_HZ)

az_anim = np.linspace(0, 360, N_FRAMES, endpoint=False)
rcs_conv_anim  = np.array([sol_conv_anim.monostatic_rcs_dbsm(a)  for a in az_anim])
rcs_stlth_anim = np.array([sol_stlth_anim.monostatic_rcs_dbsm(a) for a in az_anim])
r_min_a = min(rcs_conv_anim.min(), rcs_stlth_anim.min()) - 3
r_max_a = max(rcs_conv_anim.max(), rcs_stlth_anim.max()) + 3
os.makedirs('./output', exist_ok=True)

frames = []
for i, az in enumerate(az_anim):
    fig = plt.figure(figsize=(12, 5), facecolor=BG)
    fig.suptitle(f"Live RCS vs Radar Aspect Angle  |  X-band 10 GHz  |  Azimuth = {az:5.1f}°",
                  color=TEXT, fontsize=12, fontweight='bold')

    # 3D view - conventional (rotating)
    ax1 = fig.add_subplot(1, 3, 1, projection='3d')
    draw_geometry_3d(ax1, V_CONV, F_CONV, C_CONV)
    ax1.view_init(elev=28, azim=-az)
    ax1.set_title("Conventional", color=C_CONV, fontsize=10, fontweight='bold')

    # 3D view - stealth (rotating)
    ax2 = fig.add_subplot(1, 3, 2, projection='3d')
    draw_geometry_3d(ax2, V_STLTH, F_STLTH, C_STLTH)
    ax2.view_init(elev=28, azim=-az)
    ax2.set_title("Stealth", color=C_STLTH, fontsize=10, fontweight='bold')

    # Live polar RCS, sweeping point
    ax3 = fig.add_subplot(1, 3, 3, projection='polar')
    style_polar(ax3, "RCS (dBsm)", r_min=r_min_a, r_max=r_max_a)
    az_full = np.radians(np.linspace(0, 360, N_FRAMES, endpoint=False))
    ax3.plot(az_full, rcs_conv_anim,  color=C_CONV,  lw=1.2, alpha=0.5)
    ax3.plot(az_full, rcs_stlth_anim, color=C_STLTH, lw=1.2, alpha=0.5)
    cur = np.radians(az)
    ax3.plot([cur], [rcs_conv_anim[i]],  'o', color=C_CONV,  ms=8)
    ax3.plot([cur], [rcs_stlth_anim[i]], 'o', color=C_STLTH, ms=8)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    fname = f'./output/_frame_{i:03d}.png'
    fig.savefig(fname, dpi=80, facecolor=BG)
    plt.close(fig)
    frames.append(imageio.imread(fname))

gif_path = f'{OUT}/anim1_rotating_rcs.gif'
imageio.mimsave(gif_path, frames, duration=0.08, loop=0)

# cleanup frame files
for i in range(N_FRAMES):
    os.remove(f'./output/_frame_{i:03d}.png')
print(f"  → anim1_rotating_rcs.gif  ({len(frames)} frames)")


print("\n✓ Extended analysis complete. All outputs in", OUT)
