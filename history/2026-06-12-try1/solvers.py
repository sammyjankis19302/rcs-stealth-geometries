"""
solvers.py
==========
Two RCS computation methods:

1. PhysicalOpticsSolver  — high-frequency PO approximation for arbitrary
                           triangulated meshes. Valid when ka >> 1.
                           Coherent facet summation with phase terms.

2. mie_rcs               — exact Mie series for a conducting sphere.
                           Used for analytical validation baseline.

RCS output is always in dBsm (10·log10(σ/1 m²)).
"""

import numpy as np
from scipy.special import spherical_jn, spherical_yn


C_LIGHT = 3e8   # m/s


# ─────────────────────────────────────────────────────────────────────────────
# PHYSICAL OPTICS SOLVER
# ─────────────────────────────────────────────────────────────────────────────

class PhysicalOpticsSolver:
    """
    Monostatic RCS via Physical Optics (PO).

    σ = (4π/λ²) |Σᵢ Aᵢ (n̂ᵢ · ŝ) exp(j 2k cᵢ · ŝ)|²

    where ŝ  = unit vector from target origin toward radar
          n̂ᵢ = outward normal of facet i
          Aᵢ  = area of facet i
          cᵢ  = centroid of facet i
          k   = 2π/λ

    Only illuminated facets (n̂ᵢ · ŝ > 0) contribute (first-order shadowing).
    """

    def __init__(self, vertices, faces, frequency_hz):
        self.freq       = float(frequency_hz)
        self.wavelength = C_LIGHT / self.freq
        self.k          = 2.0 * np.pi / self.wavelength

        self.vertices = np.asarray(vertices, dtype=float)
        self.faces    = np.asarray(faces,    dtype=int)
        self._build()

    # ── geometry pre-computation ───────────────────────────────────────────

    def _build(self):
        v0 = self.vertices[self.faces[:, 0]]
        v1 = self.vertices[self.faces[:, 1]]
        v2 = self.vertices[self.faces[:, 2]]

        cross       = np.cross(v1 - v0, v2 - v0)
        mag         = np.linalg.norm(cross, axis=1, keepdims=True)
        self.normals   = cross / (mag + 1e-30)
        self.areas     = 0.5 * mag[:, 0]
        self.centroids = (v0 + v1 + v2) / 3.0

    # ── core RCS calculation ───────────────────────────────────────────────

    def monostatic_rcs_dbsm(self, az_deg, el_deg=0.0):
        """
        az_deg : azimuth  [0° = nose-on (+X), 90° = right broadside (+Y)]
        el_deg : elevation [0° = horizontal, +90° = directly above]
        returns: RCS in dBsm
        """
        az = np.radians(az_deg)
        el = np.radians(el_deg)

        # unit vector from target to radar
        shat = np.array([
            np.cos(el) * np.cos(az),
            np.cos(el) * np.sin(az),
            np.sin(el),
        ])

        cos_theta = self.normals @ shat          # shape (N_facets,)
        illum     = cos_theta > 1e-6             # illumination mask

        if not illum.any():
            return -70.0

        phase   = np.exp(1j * 2.0 * self.k * (self.centroids[illum] @ shat))
        weights = cos_theta[illum] * self.areas[illum]
        total   = np.dot(weights, phase)

        sigma   = (4.0 * np.pi / self.wavelength**2) * np.abs(total)**2
        return 10.0 * np.log10(sigma + 1e-40)

    # ── sweep helpers ──────────────────────────────────────────────────────

    def azimuth_sweep(self, n=360, el_deg=0.0):
        """Full 360° azimuth sweep at fixed elevation. Returns (angles_deg, rcs_dbsm)."""
        angles = np.linspace(0.0, 360.0, n, endpoint=False)
        rcs    = np.array([self.monostatic_rcs_dbsm(az, el_deg) for az in angles])
        return angles, rcs

    def elevation_sweep(self, az_deg=0.0, n=181):
        """Elevation sweep -90° to +90° at fixed azimuth."""
        els = np.linspace(-90.0, 90.0, n)
        rcs = np.array([self.monostatic_rcs_dbsm(az_deg, el) for el in els])
        return els, rcs

    def heatmap(self, n_az=120, n_el=60):
        """Full azimuth × elevation RCS grid. Returns (az, el, grid[n_el, n_az])."""
        azs  = np.linspace(0.0,   360.0, n_az, endpoint=False)
        els  = np.linspace(-75.0,  75.0, n_el)
        grid = np.empty((n_el, n_az))
        for i, el in enumerate(els):
            for j, az in enumerate(azs):
                grid[i, j] = self.monostatic_rcs_dbsm(az, el)
        return azs, els, grid


# ─────────────────────────────────────────────────────────────────────────────
# MIE SERIES (conducting sphere, exact)
# ─────────────────────────────────────────────────────────────────────────────

def mie_rcs_dbsm(radius_m, frequency_hz):
    """
    Backscatter RCS of a perfectly conducting sphere via Mie series.

    σ = (λ²/π) |Σₙ (-1)ⁿ (2n+1)(aₙ − bₙ)|²

    Returns RCS in dBsm.
    """
    lam = C_LIGHT / frequency_hz
    ka  = 2.0 * np.pi * radius_m / lam
    n_max = max(int(ka + 4.0 * ka**(1.0/3.0) + 4.0), 5)

    S = 0j
    for n in range(1, n_max + 1):
        jn  = spherical_jn(n, ka)
        jnp = spherical_jn(n, ka, derivative=True)
        yn  = spherical_yn(n, ka)
        ynp = spherical_yn(n, ka, derivative=True)

        hn  = jn  + 1j * yn
        hnp = jnp + 1j * ynp

        an = (ka * jnp + jn)  / (ka * hnp + hn)
        bn =  jn              /  hn

        S += (-1)**n * (2*n + 1) * (an - bn)

    sigma = (lam**2 / np.pi) * np.abs(S)**2
    return 10.0 * np.log10(sigma + 1e-40)


def mie_frequency_sweep(radius_m, freqs_hz):
    """Returns array of RCS [dBsm] for each frequency."""
    return np.array([mie_rcs_dbsm(radius_m, f) for f in freqs_hz])


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE: build solver with updated frequency
# ─────────────────────────────────────────────────────────────────────────────

def frequency_sweep(vertices, faces, freqs_hz, az_deg=0.0, el_deg=0.0):
    """Compute RCS at multiple frequencies for a fixed look angle."""
    rcs = []
    for f in freqs_hz:
        s = PhysicalOpticsSolver(vertices, faces, f)
        rcs.append(s.monostatic_rcs_dbsm(az_deg, el_deg))
    return np.array(rcs)
