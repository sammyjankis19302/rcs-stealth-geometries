"""
Checks of the solver against answers known exactly, added in November 2026.

  1. A 2 m x 2 m flat plate at 10 GHz: monostatic RCS against the angle from the normal, compared
     with the textbook Physical Optics (PO) result
         sigma = 4 pi A^2 / lambda^2 * cos^2(t) * [sin(kL sin t) / (kL sin t)]^2.
  2. A 1 m conducting sphere at 10 GHz: the exact Mie series (pi a^2 = 4.97 dBsm at this size)
     against PO on the 2,304-facet mesh used in the project and on a 36,864-facet mesh.
  3. The conventional aircraft at 1 GHz with its flat faces cut into ever smaller facets: with
     each facet treated as a point (the project's model) the answer keeps changing as the mesh is
     refined, and settles on the value the exact facet integral gives on the original 32 facets.
  4. The four aircraft, PO only, round the azimuth circle, with all the November corrections.

Each check runs the facet model both ways: 'centroid' (each facet a point carrying its whole area,
as in June and July 2026) and 'exact' (the phase integrated over each triangle).

Run from this folder:  python validate.py
It writes ../figures/november/validation.png and corrected-po-comparison.png and prints a summary.
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import geometries as G
import solvers as S

F_HZ = 10e9
LAM = S.C_LIGHT / F_HZ
K = 2 * np.pi / LAM
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures', 'november')
ORANGE, BLUE, AQUA, YELLOW = '#eb6834', '#2a78d6', '#1baf7a', '#eda100'
INK, MUTED = '#1f2328', '#59636e'


def po(V, F, mode, f_hz=F_HZ):
    S.FACET_INTEGRAL = mode
    return S.POAmplitudeSolver(V, F, f_hz)


def mean_db(d):
    return 10 * np.log10(np.mean(10 ** (np.asarray(d) / 10)))


def plate():
    V, F = G.flat_plate(2.0, 2.0)                       # x-y plane, normal +z
    theta = np.linspace(0.0, 15.0, 601)                 # tilt away from the normal
    curves = {m: np.array([po(V, F, m).monostatic_rcs_dbsm(0.0, 90.0 - t) for t in theta])
              for m in ('centroid', 'exact')}
    t = np.radians(theta)
    x = K * 2.0 * np.sin(t)
    textbook = 10 * np.log10(4 * np.pi * 16.0 / LAM**2 * np.cos(t)**2 * np.sinc(x / np.pi)**2 + 1e-30)
    return theta, textbook, curves


def sphere():
    az = np.linspace(0.0, 90.0, 91)
    out = []
    for (n_lat, n_lon), mode in [((24, 48), 'centroid'), ((24, 48), 'exact'), ((96, 192), 'exact')]:
        V, F = G.sphere_mesh(1.0, n_lat, n_lon)
        s = po(V, F, mode)
        out.append((len(F), mode, np.array([s.monostatic_rcs_dbsm(a, 0.0) for a in az])))
    return az, S.mie_rcs_dbsm(1.0, F_HZ), out


def refinement(f_hz=1e9):
    az = np.arange(0.0, 181.0, 1.0)
    exact = mean_db([po(*G.conventional_aircraft(1), 'exact', f_hz).monostatic_rcs_dbsm(a, 0.0) for a in az])
    rows = []
    for sd in (1, 2, 4, 8, 16, 32, 64):
        V, F = G.conventional_aircraft(sd)
        s = po(V, F, 'centroid', f_hz)
        rows.append((len(F), mean_db([s.monostatic_rcs_dbsm(a, 0.0) for a in az])))
    return exact, rows


def aircraft():
    az = np.arange(0.0, 360.0, 0.5)
    shapes = {'conventional': G.conventional_aircraft(), 'stealth': G.stealth_aircraft(),
              'flying wing': G.flying_wing(), 'chined nose': G.chined_nose_aircraft()}
    res = {}
    for name, (V, F) in shapes.items():
        s = po(V, F, 'exact')
        res[name] = np.maximum([s.monostatic_rcs_dbsm(a, 0.0) for a in az], -60.0)
    return az, res


def main():
    theta, textbook, plate_curves = plate()
    az_s, mie, sphere_runs = sphere()
    exact_mean, refine = refinement()
    az_a, air = aircraft()
    S.FACET_INTEGRAL = 'exact'

    print(f'1. plate at broadside: textbook {textbook[0]:.2f} dBsm, centroid {plate_curves["centroid"][0]:.2f}, '
          f'exact {plate_curves["exact"][0]:.2f}')
    for t in (0.5, 2.0, 5.0):
        i = np.argmin(np.abs(theta - t))
        print(f'   plate at {t:3.1f} deg: textbook {textbook[i]:6.2f}, centroid {plate_curves["centroid"][i]:6.2f}, '
              f'exact {plate_curves["exact"][i]:6.2f} dBsm')
    print(f'2. sphere, Mie series: {mie:.2f} dBsm')
    for n, mode, v in sphere_runs:
        print(f'   sphere, PO {mode:8s} on {n:6,d} facets: {v.min():6.2f} to {v.max():6.2f} dBsm')
    print(f'3. conventional aircraft at 1 GHz, mean RCS over azimuth; exact integral on 32 facets: {exact_mean:.1f} dBsm')
    for n, m in refine:
        print(f'   facets as points, {n:7,d} facets: {m:5.1f} dBsm')
    print('4. corrected PO, 10 GHz, 0 deg elevation (dBsm):')
    for name, r in air.items():
        print(f'   {name:12s} nose-on {r[0]:6.1f}  broadside {r[180]:6.1f}  tail-on {r[360]:6.1f}  mean {mean_db(r):6.1f}')

    # figure 1: the three checks
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(16, 4.6))
    a1.plot(theta, textbook, color=INK, lw=2.6, label='textbook PO formula')
    a1.plot(theta, plate_curves['centroid'], color=ORANGE, lw=1.1, label='facets as points (June/July model)')
    a1.plot(theta, plate_curves['exact'], color=BLUE, lw=1.1, ls='--', label='facets integrated exactly')
    a1.set_ylim(textbook.max() - 55, textbook.max() + 9)
    a1.set_xlabel('angle from the plate normal [deg]')
    a1.set_ylabel('RCS [dBsm]')
    a1.set_title('1. 2 m x 2 m flat plate, 10 GHz', loc='left', fontsize=11, fontweight='bold')
    a1.legend(frameon=False, fontsize=8.5, loc='upper right')

    style = {('centroid', 2304): ORANGE, ('exact', 2304): BLUE, ('exact', 36864): AQUA}
    for n, mode, v in sphere_runs:
        lab = ('facets as points' if mode == 'centroid' else 'facets integrated exactly') + f', {n:,} facets'
        a2.plot(az_s, v, color=style[mode, n], lw=1.3, label=lab)
    a2.axhline(mie, color=INK, lw=2.6, label=f'Mie series (exact): {mie:.2f} dBsm')
    a2.set_ylim(0, 40)
    a2.set_xlabel('azimuth [deg]')
    a2.set_ylabel('RCS [dBsm]')
    a2.set_title('2. 1 m conducting sphere, 10 GHz', loc='left', fontsize=11, fontweight='bold')
    a2.legend(frameon=False, fontsize=8.5, loc='upper right')

    n_f = [r[0] for r in refine]
    a3.semilogx(n_f, [r[1] for r in refine], color=ORANGE, lw=1.6, marker='o', ms=8,
                label='facets as points, mesh refined')
    a3.axhline(exact_mean, color=BLUE, lw=1.6, ls='--', label=f'facets integrated exactly, 32 facets: {exact_mean:.1f} dBsm')
    a3.set_xlabel('number of facets')
    a3.set_ylabel('mean RCS over azimuth [dBsm]')
    a3.set_title('3. conventional aircraft, 1 GHz, PO only', loc='left', fontsize=11, fontweight='bold')
    a3.legend(frameon=False, fontsize=8.5, loc='upper right')
    a3.set_ylim(exact_mean - 4, max(r[1] for r in refine) + 6)
    for ax in (a1, a2, a3):
        ax.grid(alpha=0.25)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, 'validation.png'), dpi=150)

    # figure 2: corrected PO round the circle, one panel per aircraft
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True, sharey=True)
    colors = {'conventional': ORANGE, 'stealth': BLUE, 'flying wing': AQUA, 'chined nose': YELLOW}
    for ax, (name, r) in zip(axes.flat, air.items()):
        ax.plot(az_a, r, color=colors[name], lw=1.0)
        ax.set_title(f'{name}', loc='left', fontsize=11, fontweight='bold')
        txt = f'nose-on {r[0]:.0f}   broadside {r[180]:.0f}   tail-on {r[360]:.0f} dBsm'
        ax.text(0.99, 0.96, txt, transform=ax.transAxes, ha='right', va='top', fontsize=8.5, color=MUTED)
        ax.set_xticks(range(0, 361, 45))
        ax.grid(alpha=0.25)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
    for ax in axes[1]:
        ax.set_xlabel('azimuth [deg]   (0 = nose-on, 90 = right broadside, 180 = tail-on)')
    for ax in axes[:, 0]:
        ax.set_ylabel('RCS [dBsm]')
    axes[0, 0].set_ylim(-60, 70)
    fig.suptitle('Physical Optics only, 10 GHz, 0 deg elevation, with the November 2026 corrections '
                 '(edges and corners not included)', fontsize=10.5, color=MUTED, x=0.01, ha='left')
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, 'corrected-po-comparison.png'), dpi=150)
    print('wrote figures/november/validation.png and figures/november/corrected-po-comparison.png')


if __name__ == '__main__':
    main()
