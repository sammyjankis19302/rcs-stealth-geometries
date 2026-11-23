"""
The explanatory figures and the animation in the README, drawn in November 2026.

Run from anywhere:   python tools/make_figures.py

Writes
  figures/explained/what-rcs-is.png        the radar, the echo, the dBsm scale, why dB matter
  figures/explained/why-shape-matters.png  a flat plate square-on and tilted, computed
  figures/explained/three-views.png        top, side and front views of the four aircraft
  figures/timeline.png                     how the project grew
  figures/november/then-and-now.png        June model as presented against the corrected PO
  figures/november/radar-sweep.gif         the radar going round two of the aircraft

All the RCS numbers come from the corrected solver in rcs/, except the June curves in
then-and-now.png, which come from running the June code in history/2026-06-20-june-final.
"""
import json
import os
import subprocess
import sys
from datetime import date

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch, Polygon
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'rcs'))
import geometries as G   # noqa: E402
import solvers as S      # noqa: E402

ORANGE, BLUE, AQUA, YELLOW = '#eb6834', '#2a78d6', '#1baf7a', '#eda100'
INK, MUTED, FAINT = '#1f2328', '#59636e', '#d0d7de'
F_HZ = 10e9
LAM = S.C_LIGHT / F_HZ
AIRCRAFT = [('conventional', G.conventional_aircraft, ORANGE),
            ('stealth', G.stealth_aircraft, BLUE),
            ('flying wing', G.flying_wing, AQUA),
            ('chined nose', G.chined_nose_aircraft, YELLOW)]
plt.rcParams.update({'font.size': 10, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.titlecolor': INK})


def out(*parts):
    path = os.path.join(ROOT, 'figures', *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def tidy(ax):
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    ax.grid(alpha=0.25)


def po_sweep(V, F, az, el=0.0, f_hz=F_HZ):
    S.FACET_INTEGRAL = 'exact'
    s = S.POAmplitudeSolver(V, F, f_hz)
    return np.array([s.monostatic_rcs_dbsm(a, el) for a in az])


def top_view(ax, V, F, color, lw=0.6, alpha=0.9):
    """Plan view, nose up: plot x = aircraft y (right wing to the right), plot y = -x."""
    order = np.argsort(V[F].mean(axis=1)[:, 2])
    for f in F[order]:
        p = V[f]
        ax.add_patch(Polygon(np.c_[p[:, 1], -p[:, 0]], closed=True, fc=color, ec=INK,
                             lw=lw, alpha=alpha))


def db_to_m2(d):
    return 10 ** (d / 10)


# ── 1. what RCS is ────────────────────────────────────────────────────────────

def what_rcs_is():
    fig = plt.figure(figsize=(15, 5.2))
    a = fig.add_axes([0.01, 0.05, 0.42, 0.86])
    a.set_xlim(0, 10); a.set_ylim(0, 6); a.set_aspect('equal'); a.axis('off')
    # radar
    a.add_patch(Arc((1.0, 3.0), 1.6, 2.4, theta1=-70, theta2=70, lw=3, color=INK))
    a.plot([1.0, 0.55, 1.45, 1.0], [3.0, 1.4, 1.4, 3.0], color=INK, lw=2)
    a.text(1.0, 0.9, 'radar', ha='center', color=INK)
    # pulse going out
    for r in (1.2, 2.0, 2.8, 3.6, 4.4):
        a.add_patch(Arc((1.2, 3.0), 2 * r, 2 * r, theta1=-22, theta2=22, lw=1.6, color=BLUE,
                        alpha=1 - r / 6))
    # aircraft, plan view seen from above, nose towards the radar
    V, F = G.conventional_aircraft()
    sc = 0.33
    for f in F:
        p = V[f]
        a.add_patch(Polygon(np.c_[7.9 + p[:, 0] * sc, 3.0 + p[:, 1] * sc], closed=True,
                            fc=ORANGE, ec=INK, lw=0.4, alpha=0.9))
    # scattered in all directions, a little coming back
    for ang in (150, 110, 70, 30, -30, -70, -110, -150):
        t = np.radians(ang)
        a.add_patch(FancyArrowPatch((7.9 + 1.3 * np.cos(t), 3.0 + 1.3 * np.sin(t)),
                                    (7.9 + 2.0 * np.cos(t), 3.0 + 2.0 * np.sin(t)),
                                    arrowstyle='-|>', mutation_scale=10, color=MUTED, lw=1))
    a.add_patch(FancyArrowPatch((6.4, 2.55), (1.9, 2.55), arrowstyle='-|>', mutation_scale=14,
                                color=ORANGE, lw=2.2))
    a.text(4.15, 2.15, 'the echo: a tiny part of the pulse comes back', ha='center',
           color=ORANGE, fontsize=9.5)
    a.text(4.15, 3.95, 'the pulse goes out', ha='center', color=BLUE, fontsize=9.5)
    a.text(0.1, 5.65, 'Radar cross section, σ', fontsize=13, fontweight='bold', color=INK)
    a.text(0.1, 5.15, 'the area of a perfect, all-direction reflector that would send back\n'
           'the same echo as the aircraft does from that direction', fontsize=9.5, color=MUTED,
           va='top')
    a.text(0.1, 0.25, 'in decibels:  σ [dBsm] = 10 log₁₀( σ / 1 m² )', fontsize=10.5, color=INK)

    # the dBsm scale with numbers from this project
    b = fig.add_axes([0.50, 0.12, 0.17, 0.74])
    marks = [(57.6, 'conventional aircraft, broadside'), (53.5, '2 m × 2 m flat plate, square-on'),
             (40.5, 'conventional aircraft, nose-on'), (4.97, '1 m sphere, from any side'),
             (-18.1, 'stealth aircraft, nose-on (facets only)')]
    b.set_ylim(-30, 70); b.set_xlim(0, 1)
    b.set_yticks(range(-30, 71, 10))
    b.set_ylabel('RCS [dBsm]')
    b.set_xticks([])
    for sp in ('top', 'right', 'bottom'):
        b.spines[sp].set_visible(False)
    text_y = {57.6: 64.0, 53.5: 54.5}
    for v, lab in marks:
        b.plot([0, 0.18], [v, v], color=INK, lw=2)
        ty = text_y.get(v, v)
        b.plot([0.18, 0.23], [v, ty], color=MUTED, lw=0.8)
        m2 = db_to_m2(v)
        m2s = f'{m2:,.0f} m²' if m2 >= 10 else (f'{m2:.2f} m²' if m2 >= 0.1 else f'{m2:.3f} m²')
        b.text(0.25, ty, f'{v:g} dBsm  ({m2s})\n{lab}', va='center', fontsize=8.6, color=INK)
    b.set_title('The scale, with numbers from this project', loc='left', fontsize=11,
                fontweight='bold', x=-0.35)
    b.text(-0.35, -41, 'every 10 dBsm is ten times the area', fontsize=8.6, color=MUTED,
           transform=b.transData)

    # why a few dB matter
    c = fig.add_axes([0.80, 0.14, 0.19, 0.70])
    d = np.linspace(0, 40, 200)
    c.plot(d, 100 * 10 ** (-d / 40), color=BLUE, lw=2)
    for x in (10, 20, 30):
        y = 100 * 10 ** (-x / 40)
        c.plot(x, y, 'o', color=BLUE, ms=7, mec='white', mew=1.5)
        c.annotate(f'{y:.0f}%', (x, y), xytext=(6, 6), textcoords='offset points', fontsize=9,
                   color=INK)
    c.set_xlabel('RCS reduction [dB]')
    c.set_ylabel('detection range [% of original]')
    c.set_ylim(0, 105)
    c.set_title('Why a few dB matter', loc='left', fontsize=11, fontweight='bold')
    c.text(0.98, 0.97, 'range $\\propto\\ \\sigma^{1/4}$\n(radar range equation)', transform=c.transAxes, ha='right',
           va='top', fontsize=9, color=MUTED)
    tidy(c)
    fig.savefig(out('explained', 'what-rcs-is.png'), dpi=140)
    plt.close(fig)


# ── 2. why shape matters ─────────────────────────────────────────────────────

def why_shape_matters():
    fig = plt.figure(figsize=(14, 4.9))
    a = fig.add_axes([0.01, 0.04, 0.40, 0.9])
    a.set_xlim(0, 10); a.set_ylim(0, 7); a.set_aspect('equal'); a.axis('off')
    for y0, tilt, title in ((5.0, 0, 'square-on: the echo comes straight back'),
                            (1.9, 10, 'tilted by θ: the echo leaves at 2θ and misses the radar')):
        a.add_patch(Arc((0.9, y0), 1.0, 1.5, theta1=-70, theta2=70, lw=2.5, color=INK))
        a.text(0.9, y0 - 1.2, 'radar', ha='center', fontsize=9, color=INK)
        t = np.radians(tilt)
        cx = 7.6
        a.plot([cx - 1.2 * np.sin(t), cx + 1.2 * np.sin(t)], [y0 + 1.2 * np.cos(t), y0 - 1.2 * np.cos(t)],
               color=INK, lw=5, solid_capstyle='butt')
        a.add_patch(FancyArrowPatch((1.6, y0 + 0.12), (cx - 0.15, y0 + 0.12), arrowstyle='-|>',
                                    mutation_scale=14, color=BLUE, lw=2))
        back = np.radians(180 - 2 * tilt)
        a.add_patch(FancyArrowPatch((cx - 0.15, y0 - 0.12),
                                    (cx - 0.15 + 4.6 * np.cos(back), y0 - 0.12 - 4.6 * np.sin(np.radians(2 * tilt))),
                                    arrowstyle='-|>', mutation_scale=14, color=ORANGE, lw=2))
        a.text(0.1, y0 + 1.25, title, fontsize=10, color=INK)
    a.text(8.2, 5.0, 'flat\nface', fontsize=9, color=MUTED, va='center')

    b = fig.add_axes([0.50, 0.14, 0.47, 0.74])
    V, F = G.flat_plate(2.0, 2.0)
    tilt = np.linspace(0, 20, 801)
    S.FACET_INTEGRAL = 'exact'
    s = S.POAmplitudeSolver(V, F, F_HZ)
    plate = np.array([s.monostatic_rcs_dbsm(0.0, 90.0 - t) for t in tilt])
    sphere = S.mie_rcs_dbsm(1.0, F_HZ)
    b.plot(tilt, plate, color=INK, lw=1.4, label='2 m × 2 m flat plate, tilted')
    b.axhline(sphere, color=AQUA, lw=2, ls='--', label=f'1 m sphere: {sphere:.1f} dBsm from any side')
    i5 = np.argmin(np.abs(tilt - 5))
    b.annotate(f'square-on: {plate[0]:.1f} dBsm', (0, plate[0]), xytext=(1.2, 57), fontsize=9.5,
               color=INK, arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.8))
    b.annotate(f'tilted 5°: {plate[i5]:.1f} dBsm,\n{plate[0] - plate[i5]:.0f} dB less', (5, plate[i5]),
               xytext=(7.5, 40), fontsize=9.5, color=INK,
               arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.8))
    b.set_ylim(-25, 65)
    b.set_xlabel('tilt away from square-on [deg]')
    b.set_ylabel('RCS at 10 GHz [dBsm]')
    b.set_title('A flat face is a mirror: huge square-on, small a few degrees off', loc='left',
                fontsize=11, fontweight='bold')
    b.legend(frameon=False, loc='upper right', fontsize=9)
    tidy(b)
    fig.savefig(out('explained', 'why-shape-matters.png'), dpi=140)
    plt.close(fig)


# ── 3. three views of the four aircraft ──────────────────────────────────────

def three_views():
    fig, axes = plt.subplots(3, 4, figsize=(15, 7.0), gridspec_kw={'height_ratios': [9.4, 2.8, 2.8]})
    views = [('top', lambda p: np.c_[p[:, 1], -p[:, 0]], lambda c: c[:, 2]),
             ('side', lambda p: np.c_[p[:, 0], p[:, 2]], lambda c: -c[:, 1]),
             ('front', lambda p: np.c_[-p[:, 1], p[:, 2]], lambda c: c[:, 0])]
    lims = {'top': ((-6.5, 6.5), (-3.8, 5.6)), 'side': ((-7.3, 5.7), (-0.8, 2.0)),
            'front': ((-6.5, 6.5), (-0.8, 2.0))}
    for j, (name, fn, color) in enumerate(AIRCRAFT):
        V, F = fn()
        for i, (view, proj, depth) in enumerate(views):
            ax = axes[i, j]
            cent = V[F].mean(axis=1)
            for f in F[np.argsort(-depth(cent) if view != 'top' else depth(cent))]:
                ax.add_patch(Polygon(proj(V[f]), closed=True, fc=color, ec=INK, lw=0.5, alpha=0.75))
            (x0, x1), (y0, y1) = lims[view]
            ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
            for sp in ('top', 'right'):
                ax.spines[sp].set_visible(False)
            ax.tick_params(labelsize=7.5)
            if i == 0:
                L = V[:, 0].max() - V[:, 0].min()
                B = V[:, 1].max() - V[:, 1].min()
                ax.set_title(f'{name}\n{len(F)} facets, {L:.1f} m long, {B:.1f} m span', fontsize=10.5,
                             fontweight='bold')
            if j == 0:
                ax.set_ylabel(f'{view} view [m]')
    fig.text(0.01, 0.005, 'Top views have the nose up; side views have the nose to the left; front views are '
             'seen from ahead of the aircraft. The same scale throughout.', fontsize=9, color=MUTED)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(out('explained', 'three-views.png'), dpi=130)
    plt.close(fig)


# ── 4. timeline ──────────────────────────────────────────────────────────────

def timeline():
    events = [(date(2026, 6, 12), 'Try 1', 'Physical Optics, a sphere\nchecked against Mie, four shapes', 1),
              (date(2026, 6, 14), 'Tries 2 and 3', 'bistatic sweeps, flying wing,\nchined nose, first animation;\n'
               'edges, double bounce, absorbers', -1),
              (date(2026, 6, 20), 'Tries 4 to 8', 'the June program\nand its 64 figures', 1),
              (date(2026, 6, 23), 'First report', "Uday's June draft", -1),
              (date(2026, 7, 16), 'July extension', 'polarimetric, triple bounce,\nSIBC, optimizer, wideband,\n'
               'ISAR, convergence studies', 1),
              (date(2026, 7, 17), 'Handed in', 'final report,\nslides and poster', -1),
              (date(2026, 11, 24), 'Checked', 'against exact answers;\ncorrected and published', 1)]

    def x_of(d):
        n = (d - date(2026, 6, 8)).days
        return n if n <= 44 else 50 + (d - date(2026, 11, 20)).days

    fig, ax = plt.subplots(figsize=(15, 3.6))
    ax.plot([0, 45], [0, 0], color=MUTED, lw=2)
    ax.plot([49, 56], [0, 0], color=MUTED, lw=2)
    ax.text(47, 0, '···', ha='center', va='center', color=MUTED, fontsize=14)
    for m, lab in ((date(2026, 6, 8), 'June'), (date(2026, 7, 1), 'July')):
        ax.text(x_of(m), -0.22, lab, color=MUTED, fontsize=9)
    ax.text(x_of(date(2026, 11, 20)), -0.22, 'November', color=MUTED, fontsize=9)
    colors = [BLUE, BLUE, BLUE, BLUE, AQUA, AQUA, ORANGE]
    for (d, title, body, side), c in zip(events, colors):
        x = x_of(d)
        ax.plot(x, 0, 'o', color=c, ms=11, mec='white', mew=2, zorder=3)
        ax.plot([x, x], [0, 0.32 * side], color=c, lw=1.2)
        ax.text(x, 0.38 * side, f'{title}  ·  {d.day} {d.strftime("%b")}\n{body}', ha='center',
                va='bottom' if side > 0 else 'top', fontsize=8.8, color=INK,
                fontweight='normal', linespacing=1.3)
    ax.set_xlim(-2, 59); ax.set_ylim(-1.45, 1.45); ax.axis('off')
    fig.tight_layout()
    fig.savefig(out('timeline.png'), dpi=140)
    plt.close(fig)


# ── 5. then and now ──────────────────────────────────────────────────────────

JUNE_CODE = r"""
import json, numpy as np, geometries as G, solvers as S
az = np.arange(0, 360, 1.0)
res = {}
for name, fn in [('conventional', G.conventional_aircraft), ('stealth', G.stealth_aircraft),
                 ('flying wing', G.flying_wing), ('chined nose', G.chined_nose_aircraft)]:
    V, F = fn()
    s = S.make_solver(V, F, 10e9, level='full')
    res[name] = [float(s.monostatic_rcs_dbsm(a, 0.0)) for a in az]
print(json.dumps(res))
"""


def then_and_now():
    june_dir = os.path.join(ROOT, 'history', '2026-06-20-june-final')
    run = subprocess.run([sys.executable, '-c', JUNE_CODE], cwd=june_dir, capture_output=True,
                         text=True, check=True)
    june = json.loads(run.stdout.strip().splitlines()[-1])
    az = np.arange(0, 360, 1.0)
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.9), subplot_kw={'projection': 'polar'})
    for ax, (name, fn, color) in zip(axes, AIRCRAFT):
        now = np.maximum(po_sweep(*fn(), az), -40)
        then = np.maximum(np.array(june[name]), -40)
        t = np.radians(np.r_[az, 360])
        ax.plot(t, np.r_[then, then[0]], color=MUTED, lw=1.0, label='June, as presented')
        ax.plot(t, np.r_[now, now[0]], color=color, lw=1.6, label='November, corrected (facets only)')
        ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
        ax.set_rlim(-40, 70); ax.set_rorigin(-55)
        ax.set_rticks([-20, 0, 20, 40, 60])
        ax.tick_params(labelsize=7.5, colors=MUTED)
        ax.set_xticks(np.radians([0, 90, 180, 270]))
        ax.set_xticklabels(['nose-on', '90°', 'tail-on', '270°'], fontsize=8.5)
        ax.grid(alpha=0.3)
        ax.set_title(name, fontsize=11, fontweight='bold', pad=14)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, ['June, as presented (gray)', 'November, corrected, Physical Optics only (colour)'],
               loc='lower center', ncol=2, frameon=False, fontsize=9.5)
    fig.suptitle('RCS at 10 GHz, 0° elevation, dBsm. June: edges and double bounce included, facets as points, '
                 'and "nose-on" as the program labelled it. November: Physical Optics only, corrected.',
                 fontsize=9.5, color=MUTED, y=0.995)
    fig.tight_layout(rect=(0, 0.07, 1, 0.97))
    fig.savefig(out('november', 'then-and-now.png'), dpi=140)
    plt.close(fig)


# ── 6. the radar going round ─────────────────────────────────────────────────

def radar_sweep(step=4):
    az_fine = np.arange(0, 360.5, 0.5)
    pairs = [AIRCRAFT[0], AIRCRAFT[1]]
    curves = [np.maximum(po_sweep(*fn(), az_fine), -40) for _, fn, _ in pairs]
    fig = plt.figure(figsize=(9.6, 5.6), dpi=100)
    polars, lines, beams, labels = [], [], [], []
    for k, ((name, fn, color), r) in enumerate(zip(pairs, curves)):
        ax = fig.add_axes([0.06 + 0.5 * k, 0.10, 0.38, 0.70], projection='polar')
        ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
        ax.set_rlim(-40, 70); ax.set_rorigin(-80)
        ax.set_rticks([-20, 0, 20, 40, 60]); ax.set_rlabel_position(135)
        ax.tick_params(labelsize=7, colors=MUTED)
        ax.set_xticks(np.radians([0, 90, 180, 270]))
        ax.set_xticklabels(['nose-on', '90°', 'tail-on', '270°'], fontsize=8)
        ax.grid(alpha=0.3)
        ax.set_title(f'{name} aircraft', fontsize=12, fontweight='bold', pad=22, color=INK)
        line, = ax.plot([], [], color=color, lw=1.6)
        beam, = ax.plot([], [], color=INK, lw=1.0, alpha=0.5)
        dot, = ax.plot([], [], 'o', color=INK, ms=5)
        lab = fig.text(0.25 + 0.5 * k, 0.02, '', ha='center', fontsize=10, color=INK, family='monospace')
        polars.append(ax); lines.append(line); beams.append((beam, dot)); labels.append(lab)
        # plan view in the middle
        pos = ax.get_position()
        w = pos.width * 0.25
        h = w * fig.get_figwidth() / fig.get_figheight()
        inset = fig.add_axes([pos.x0 + pos.width / 2 - w / 2, pos.y0 + pos.height / 2 - h / 2, w, h])
        V, F = fn()
        top_view(inset, V, F, color, lw=0.4)
        span = 1.04 * np.hypot(V[:, 0], V[:, 1]).max()
        inset.set_xlim(-span, span); inset.set_ylim(-span, span); inset.set_aspect('equal'); inset.axis('off')
    fig.text(0.5, 0.965, 'Physical Optics at 10 GHz, corrected solver: the radar goes round, the echo is '
             'drawn in dBsm', ha='center', fontsize=10, color=MUTED)
    frames = []
    for a in range(0, 361, step):
        i = int(a / 0.5)
        for (line, (beam, dot), lab, r) in zip(lines, beams, labels, curves):
            line.set_data(np.radians(az_fine[:i + 1]), r[:i + 1])
            beam.set_data([np.radians(a)] * 2, [-40, 70])
            dot.set_data([np.radians(a)], [70])
            lab.set_text(f'radar at {a % 360:3d}°   echo {r[i]:6.1f} dBsm')
        fig.canvas.draw()
        frames.append(Image.frombuffer('RGBA', fig.canvas.get_width_height(),
                                       fig.canvas.buffer_rgba()).convert('RGB'))
    plt.close(fig)
    pal = frames[len(frames) // 2].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q += [q[-1]] * 12                                   # hold the finished picture for a moment
    q[0].save(out('november', 'radar-sweep.gif'), save_all=True, append_images=q[1:], duration=70,
              loop=0, optimize=True)


if __name__ == '__main__':
    what_rcs_is()
    why_shape_matters()
    three_views()
    timeline()
    then_and_now()
    radar_sweep()
    print('done')
