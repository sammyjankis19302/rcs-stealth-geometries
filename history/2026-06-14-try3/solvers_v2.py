"""
solvers_v2.py
=============
Advanced RCS physics — three upgrades on top of basic PO:

  1. PTD  — Physical Theory of Diffraction (Ufimtsev fringe field correction)
            Adds edge-diffracted contributions missed by PO.
            Critical for stealth aircraft: wing LE/TE diffraction dominates
            at nose-on aspect where PO gives near-zero.

  2. Double Bounce — Second-order geometric-optics reflections.
            Ray from facet i specularly reflects onto facet j, then back to
            radar.  This is what produces the corner-reflector enhancement
            on conventional aircraft (fin/fuselage junction, wing/fuselage).

  3. Frequency-Dependent RAM — Two material models:
            a) Salisbury Screen  : resistive sheet + λ/4 spacer + ground plane.
                                   Narrowband, analytic minimum at f₀.
            b) Dallenbach Layer  : homogeneous lossy slab (εᵣ, μᵣ complex).
                                   Broadband with realistic material parameters.

All solvers return complex scatter amplitude so contributions are combined
coherently before squaring to get RCS.
"""

import numpy as np
from scipy.special import spherical_jn, spherical_yn

C_LIGHT = 3e8
Z0      = 376.73   # free-space impedance [Ω]


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY: complex sinc  (sinc(0) = 1 by l'Hôpital)
# ─────────────────────────────────────────────────────────────────────────────

def _sinc(x):
    """sin(x)/x with safe limit at x=0."""
    return np.where(np.abs(x) < 1e-9, 1.0, np.sin(x) / x)


# ─────────────────────────────────────────────────────────────────────────────
# BASE SOLVER  (upgraded: returns complex amplitude, not just dBsm)
# ─────────────────────────────────────────────────────────────────────────────

class POAmplitudeSolver:
    """
    Physical Optics coherent scatter amplitude (complex-valued).
    This is the base class shared by all higher-order solvers.

    Internal method  _po_amplitude(shat, shat_rx=None)  returns the raw
    complex PO sum, allowing downstream classes to add their own corrections
    before the final |·|² squaring.
    """

    def __init__(self, vertices, faces, frequency_hz, ram_model=None):
        self.freq       = float(frequency_hz)
        self.wavelength = C_LIGHT / self.freq
        self.k          = 2.0 * np.pi / self.wavelength
        self.vertices   = np.asarray(vertices, dtype=float)
        self.faces      = np.asarray(faces,    dtype=int)
        self.ram        = ram_model       # optional FreqDependentRAM instance
        self._build_facets()

    def _build_facets(self):
        v0 = self.vertices[self.faces[:, 0]]
        v1 = self.vertices[self.faces[:, 1]]
        v2 = self.vertices[self.faces[:, 2]]
        cross          = np.cross(v1 - v0, v2 - v0)
        mag            = np.linalg.norm(cross, axis=1, keepdims=True)
        self.normals   = cross / (mag + 1e-30)
        self.areas     = 0.5 * mag[:, 0]
        self.centroids = (v0 + v1 + v2) / 3.0
        # per-facet reflectivity (modified by RAM model)
        self.reflectivity = np.ones(len(self.faces))

    def _update_ram(self):
        """Update per-facet reflectivity from RAM model at current frequency."""
        if self.ram is not None:
            amp = self.ram.amplitude_reflectivity(self.freq)
            self.reflectivity[:] = amp

    def _po_amplitude(self, shat):
        """
        Returns complex PO scatter amplitude f such that σ = (4π/λ²)|f|².
        shat : unit vector from target to radar (shape (3,))
        """
        self._update_ram()
        cos_theta = self.normals @ shat
        illum     = cos_theta > 1e-6
        if not illum.any():
            return 0j
        phase   = np.exp(1j * 2.0 * self.k * (self.centroids[illum] @ shat))
        weights = self.reflectivity[illum] * cos_theta[illum] * self.areas[illum]
        return np.dot(weights, phase)

    def _amplitude_to_rcs(self, amplitude):
        sigma = (4.0 * np.pi / self.wavelength**2) * np.abs(amplitude)**2
        return 10.0 * np.log10(sigma + 1e-40)

    def _shat(self, az_deg, el_deg):
        az, el = np.radians(az_deg), np.radians(el_deg)
        return np.array([np.cos(el)*np.cos(az),
                          np.cos(el)*np.sin(az),
                          np.sin(el)])

    def monostatic_rcs_dbsm(self, az_deg, el_deg=0.0):
        return self._amplitude_to_rcs(self._po_amplitude(self._shat(az_deg, el_deg)))

    def azimuth_sweep(self, n=360, el_deg=0.0):
        angles = np.linspace(0.0, 360.0, n, endpoint=False)
        rcs    = np.array([self.monostatic_rcs_dbsm(az, el_deg) for az in angles])
        return angles, rcs

    def heatmap(self, n_az=120, n_el=60):
        azs  = np.linspace(0.0,   360.0, n_az, endpoint=False)
        els  = np.linspace(-75.0,  75.0, n_el)
        grid = np.empty((n_el, n_az))
        for i, el in enumerate(els):
            for j, az in enumerate(azs):
                grid[i, j] = self.monostatic_rcs_dbsm(az, el)
        return azs, els, grid


# ─────────────────────────────────────────────────────────────────────────────
# 1. PTD  —  Physical Theory of Diffraction  (Ufimtsev fringe field)
# ─────────────────────────────────────────────────────────────────────────────

class PTDSolver(POAmplitudeSolver):
    """
    PO + PTD combined RCS solver.

    The PTD adds the Ufimtsev fringe field correction to PO.  For each edge
    in the mesh the correction is:

        f_fringe(edge) = D_fringe(n, β) × L × sinc(kL cosβ) × e^{j2k ŝ·c}

    where:
        n     = n_wedge  = exterior wedge angle / π
        β     = angle between edge direction ê and radar direction ŝ
        L     = edge length
        c     = edge midpoint
        sinc  = sin(x)/x  (peaks when edge ⊥ radar, i.e. cosβ ≈ 0)

    For a PEC wedge in backscatter (monostatic), the Keller diffraction
    coefficient (averaged over polarization) is:

        D_fringe ≈ -e^{-jπ/4} / (n √(2πk)) × cot(π/2n) / sinβ

    Edge classification:
        boundary (1 adjacent face)  : free edge, n = 2  (half-plane)
        internal convex (2 faces, outward normals diverge) : n < 2
        internal concave (corner reflector) : n > 2  (stronger!)

    Physical meaning:
        A right-angle convex ridge (fuselage corner) has n = 1.5.
        A half-plane free edge (wing tip) has n = 2.
        A right-angle concave cavity (corner reflector) has n = 2.5.
    """

    def __init__(self, vertices, faces, frequency_hz, ram_model=None):
        super().__init__(vertices, faces, frequency_hz, ram_model)
        self._extract_edges()
        self._classify_edges()

    # ── Edge extraction ────────────────────────────────────────────────────

    def _extract_edges(self):
        """Find all unique edges and their adjacent face indices."""
        edge_map = {}
        for fi, face in enumerate(self.faces):
            for k in range(3):
                v0, v1 = int(face[k]), int(face[(k+1)%3])
                key = (min(v0,v1), max(v0,v1))
                edge_map.setdefault(key, []).append(fi)
        # edges: list of (v0, v1, [adj_face_indices])
        self.edges = [(k[0], k[1], v) for k, v in edge_map.items()]

    def _classify_edges(self):
        """
        For each edge compute:
          length, midpoint, direction, n_wedge
        """
        lengths, midpoints, directions, n_wedges = [], [], [], []

        for v0, v1, adj in self.edges:
            p0 = self.vertices[v0]
            p1 = self.vertices[v1]
            L  = np.linalg.norm(p1 - p0)
            lengths.append(L)
            midpoints.append((p0 + p1) * 0.5)
            directions.append((p1 - p0) / (L + 1e-30))

            if len(adj) == 1:
                # Boundary / free edge — half-plane, n = 2
                n_wedges.append(2.0)
            else:
                # Internal edge — compute dihedral from adjacent face normals
                n1 = self.normals[adj[0]]
                n2 = self.normals[adj[1]]
                cos_dih = np.clip(n1 @ n2, -1.0, 1.0)
                interior_dihedral = np.arccos(cos_dih)  # angle between normals

                # Determine convex vs concave:
                # Use edge midpoint and facet centroids to decide
                edge_mid = midpoints[-1]
                c1 = self.centroids[adj[0]]
                c2 = self.centroids[adj[1]]
                # Vector from edge midpoint toward face centroid average
                avg_toward = 0.5*((c1 - edge_mid) + (c2 - edge_mid))
                avg_normal = 0.5*(n1 + n2)
                # If normals point generally AWAY from the mesh interior
                # the edge is convex (standard exterior ridge)
                sign = np.sign(avg_normal @ avg_toward + 1e-12)

                if sign > 0:
                    # Concave (normals point inward toward the body centre)
                    # exterior wedge > π  →  corner reflector type
                    n_ext = (2.0 * np.pi - interior_dihedral) / np.pi
                else:
                    # Convex ridge (normals point outward)
                    n_ext = (np.pi + interior_dihedral) / np.pi

                n_wedges.append(float(np.clip(n_ext, 0.51, 3.99)))

        self.edge_L   = np.array(lengths)
        self.edge_c   = np.array(midpoints)
        self.edge_dir = np.array(directions)
        self.edge_n   = np.array(n_wedges)

    # ── Fringe diffraction coefficient ─────────────────────────────────────

    def _D_fringe(self, n, sin_beta):
        """
        Scalar Ufimtsev fringe diffraction coefficient for monostatic
        backscatter off a PEC wedge with exterior-angle parameter n.

        D = -exp(-jπ/4) / (n √(2πk)) × cot(π/2n) / sinβ

        The cot(π/2n) factor:
          n=1.0 (flat,   0° wedge): cot(π/2) = 0       → no diffraction
          n=1.5 (90° convex ridge): cot(π/3) = 1/√3 ≈ 0.577
          n=2.0 (half-plane edge) : cot(π/4) = 1.0
          n=2.5 (concave corner)  : cot(π/5) ≈ 1.376   → strongest
        """
        if sin_beta < 0.02:
            return 0j   # endfire: no contribution
        arg = np.pi / (2.0 * n)
        cot = np.cos(arg) / (np.sin(arg) + 1e-15)
        prefactor = np.exp(-1j * np.pi / 4.0) / (n * np.sqrt(2.0 * np.pi * self.k))
        return -prefactor * cot / sin_beta

    # ── Edge fringe amplitude sum ───────────────────────────────────────────

    def _edge_amplitude(self, shat):
        """Coherent sum of Ufimtsev fringe contributions from all edges."""
        total = 0j
        for i in range(len(self.edges)):
            ê   = self.edge_dir[i]
            L   = self.edge_L[i]
            c   = self.edge_c[i]
            n   = self.edge_n[i]

            cos_beta = np.dot(ê, shat)
            sin_beta = np.sqrt(max(0.0, 1.0 - cos_beta**2))

            D     = self._D_fringe(n, sin_beta)
            sinc  = _sinc(self.k * L * cos_beta)
            phase = np.exp(1j * 2.0 * self.k * np.dot(c, shat))

            total += D * L * sinc * phase
        return total

    # ── Public interface ───────────────────────────────────────────────────

    def monostatic_rcs_dbsm(self, az_deg, el_deg=0.0):
        shat = self._shat(az_deg, el_deg)
        f_po   = self._po_amplitude(shat)
        f_edge = self._edge_amplitude(shat)
        return self._amplitude_to_rcs(f_po + f_edge)

    def rcs_breakdown(self, az_deg, el_deg=0.0):
        """Returns dict with individual contributions in dBsm."""
        shat   = self._shat(az_deg, el_deg)
        f_po   = self._po_amplitude(shat)
        f_edge = self._edge_amplitude(shat)
        f_tot  = f_po + f_edge
        return {
            'PO only':     self._amplitude_to_rcs(f_po),
            'PTD edge':    self._amplitude_to_rcs(f_edge),
            'PO + PTD':    self._amplitude_to_rcs(f_tot),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. DOUBLE BOUNCE  —  Second-order geometric-optics reflections
# ─────────────────────────────────────────────────────────────────────────────

class DoubleBounce(PTDSolver):
    """
    PO + PTD + Double-bounce RCS solver.

    For each ordered pair (i, j) of facets:
      1. Check facet i is illuminated by the radar (cos θᵢ > 0).
      2. The specular reflection direction from facet i:
             ŝ_ref = ŝ - 2(n̂ᵢ · ŝ) n̂ᵢ
      3. Check facet j is illuminated by ŝ_ref (cos θⱼ_ref > 0).
      4. Check the re-scattered direction from j back to radar is valid
             (for monostatic: same as ŝ, so n̂ⱼ · ŝ > 0 also).
      5. Amplitude contribution:
             f_ij = Aᵢ cos(θᵢ) × Aⱼ cos(θⱼ_ref) × exp(j phase_ij)
         where phase_ij = 2k (ŝ·cᵢ + ŝ_ref·(cⱼ-cᵢ))
                        ≈ 2k (ŝ·cⱼ)  for monostatic (exact retrace path)

    Corner reflector signature:
        On conventional aircraft the fin-fuselage junction creates a
        near-right-angle dihedral.  Facet A (vertical fin side) reflects
        toward facet B (horizontal fuselage top) which then retro-reflects
        → massive coherent enhancement visible at 90° broadside.
        On stealth aircraft: no 90° dihedrals → double-bounce is suppressed.
    """

    def _double_bounce_amplitude(self, shat):
        cos_theta = self.normals @ shat
        illum     = cos_theta > 1e-6          # illuminated by radar
        n_facets  = len(self.faces)
        total     = 0j

        illum_idx = np.where(illum)[0]

        for i in illum_idx:
            n_i    = self.normals[i]
            c_i    = self.centroids[i]
            A_i    = self.areas[i]
            ct_i   = cos_theta[i]
            rho_i  = self.reflectivity[i]

            # Specular reflection direction FROM facet i
            s_ref = shat - 2.0 * (n_i @ shat) * n_i
            s_ref = s_ref / (np.linalg.norm(s_ref) + 1e-30)

            for j in range(n_facets):
                if j == i:
                    continue
                n_j    = self.normals[j]
                c_j    = self.centroids[j]
                A_j    = self.areas[j]
                rho_j  = self.reflectivity[j]

                # cos of angle between reflected ray and facet j normal
                cos_j_ref = n_j @ s_ref
                if cos_j_ref < 1e-6:
                    continue   # reflected ray doesn't hit facet j

                # For monostatic: the second reflection must also reach radar
                # Re-scattered from j back toward radar: n̂ⱼ · ŝ > 0
                cos_j_rx = n_j @ shat
                if cos_j_rx < 1e-6:
                    continue

                # Two-leg path phase:
                # Leg 1: radar to facet i  →  path component ŝ·cᵢ
                # Leg 2: facet i to facet j along ŝ_ref
                # Leg 3: facet j back to radar along ŝ
                # Total monostatic phase = k(ŝ·cᵢ) + k|s_ref·(cⱼ-cᵢ)| + k(ŝ·cⱼ)
                delta = c_j - c_i
                path  = (shat @ c_i) + abs(s_ref @ delta) + (shat @ c_j)
                phase = np.exp(1j * self.k * path)

                # Amplitude: product of both cos-weighted areas
                amp = rho_i * rho_j * A_i * ct_i * A_j * cos_j_ref * cos_j_rx
                total += amp * phase

        return total

    def monostatic_rcs_dbsm(self, az_deg, el_deg=0.0):
        shat   = self._shat(az_deg, el_deg)
        f_po   = self._po_amplitude(shat)
        f_edge = self._edge_amplitude(shat)
        f_db   = self._double_bounce_amplitude(shat)
        return self._amplitude_to_rcs(f_po + f_edge + f_db)

    def rcs_breakdown(self, az_deg, el_deg=0.0):
        shat   = self._shat(az_deg, el_deg)
        f_po   = self._po_amplitude(shat)
        f_edge = self._edge_amplitude(shat)
        f_db   = self._double_bounce_amplitude(shat)
        return {
            'PO only':         self._amplitude_to_rcs(f_po),
            'PTD edge':        self._amplitude_to_rcs(f_edge),
            'Double bounce':   self._amplitude_to_rcs(f_db),
            'PO + PTD':        self._amplitude_to_rcs(f_po + f_edge),
            'Full (PO+PTD+DB)':self._amplitude_to_rcs(f_po + f_edge + f_db),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3a. SALISBURY SCREEN  —  Frequency-dependent RAM (narrowband)
# ─────────────────────────────────────────────────────────────────────────────

class SalisburyScreen:
    """
    Resistive sheet + lossless λ/4 spacer + PEC ground plane.

    Physics:
      The quarter-wave spacer transforms the ground-plane short circuit into
      an open circuit at f₀.  The resistive sheet Rs = Z₀ = 377 Ω/□ then
      sees no current flowing to ground → perfect absorption at f₀.

      Input impedance:
          Z_gp(f)  = j Z₀ tan(2πf d/c)       [spacer looking into ground]
          Z_in     = Rs ‖ Z_gp                 [sheet in parallel with spacer]
          Γ(f)     = (Z_in − Z₀)/(Z_in + Z₀)

    Parameters:
        f0_hz  : design frequency for maximum absorption [Hz]
        Rs     : sheet resistance [Ω/□], default Z₀ for maximum absorption
    """

    def __init__(self, f0_hz, Rs=Z0):
        self.f0  = f0_hz
        self.Rs  = Rs
        self.d   = C_LIGHT / (4.0 * f0_hz)    # quarter-wave spacer thickness

    def reflection_coefficient(self, freq_hz):
        """Complex reflection coefficient Γ(f)."""
        beta_d = 2.0 * np.pi * freq_hz * self.d / C_LIGHT
        Z_gp   = 1j * Z0 * np.tan(beta_d)
        # Parallel combination: Z_in = Rs * Z_gp / (Rs + Z_gp)
        Z_in   = self.Rs * Z_gp / (self.Rs + Z_gp + 1e-30j)
        return (Z_in - Z0) / (Z_in + Z0)

    def amplitude_reflectivity(self, freq_hz):
        """Amplitude attenuation factor |Γ(f)| (0 = perfect absorber, 1 = bare PEC)."""
        return np.abs(self.reflection_coefficient(freq_hz))

    def absorption_db(self, freqs_hz):
        """Return absorption [dB] as a function of frequency (negative = absorption)."""
        Gamma = np.array([self.reflection_coefficient(f) for f in freqs_hz])
        return 20.0 * np.log10(np.abs(Gamma) + 1e-30)


# ─────────────────────────────────────────────────────────────────────────────
# 3b. DALLENBACH LAYER  —  Frequency-dependent RAM (broadband)
# ─────────────────────────────────────────────────────────────────────────────

class DallenbachLayer:
    """
    Homogeneous lossy slab of thickness d with complex εᵣ and μᵣ backed
    by a PEC ground plane.

    Physics:
        Propagation constant : γ = j(2πf/c)√(μᵣ εᵣ)
        Wave impedance       : Z_m = Z₀ √(μᵣ/εᵣ)
        Input impedance      : Z_in = Z_m tanh(γ d)
        Reflection coeff     : Γ = (Z_in − Z₀)/(Z_in + Z₀)

    Material presets (at X-band, ~10 GHz):
        'carbon_foam'   : εᵣ = 1.5−0.8j,  μᵣ = 1.0        (lightweight absorber)
        'ferrite_tile'  : εᵣ = 12−3j,     μᵣ = 2.5−1.5j   (heavy but wideband)
        'carbonyl_iron' : εᵣ = 8−4j,      μᵣ = 1.8−0.9j   (balanced)

    These are representative values; real materials are frequency-dispersive.
    For this model εᵣ and μᵣ are held constant over the sweep (single-pole
    approximation — adequate for comparative analysis).
    """

    PRESETS = {
        'carbon_foam':    (1.5 - 0.8j,  1.0 + 0j),
        'ferrite_tile':   (12  - 3j,    2.5 - 1.5j),
        'carbonyl_iron':  (8   - 4j,    1.8 - 0.9j),
    }

    def __init__(self, thickness_m, eps_r, mu_r):
        self.d     = thickness_m
        self.eps_r = complex(eps_r)
        self.mu_r  = complex(mu_r)

    @classmethod
    def from_preset(cls, preset_name, thickness_m=0.005):
        eps_r, mu_r = cls.PRESETS[preset_name]
        return cls(thickness_m, eps_r, mu_r)

    def reflection_coefficient(self, freq_hz):
        k0    = 2.0 * np.pi * freq_hz / C_LIGHT
        gamma = 1j * k0 * np.sqrt(self.mu_r * self.eps_r + 1e-30j)
        Z_m   = Z0 * np.sqrt(self.mu_r / (self.eps_r + 1e-30j))
        Z_in  = Z_m * np.tanh(gamma * self.d)
        return (Z_in - Z0) / (Z_in + Z0)

    def amplitude_reflectivity(self, freq_hz):
        return np.abs(self.reflection_coefficient(freq_hz))

    def absorption_db(self, freqs_hz):
        Gamma = np.array([self.reflection_coefficient(f) for f in freqs_hz])
        return 20.0 * np.log10(np.abs(Gamma) + 1e-30)


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE: Full-physics sweep functions
# ─────────────────────────────────────────────────────────────────────────────

def make_solver(vertices, faces, frequency_hz, level='full', ram_model=None):
    """
    level:  'po'   → PO only (POAmplitudeSolver)
            'ptd'  → PO + PTD edges (PTDSolver)
            'full' → PO + PTD + double bounce (DoubleBounce)
    """
    kw = dict(ram_model=ram_model)
    if level == 'po':
        return POAmplitudeSolver(vertices, faces, frequency_hz, **kw)
    elif level == 'ptd':
        return PTDSolver(vertices, faces, frequency_hz, **kw)
    else:
        return DoubleBounce(vertices, faces, frequency_hz, **kw)


def physics_frequency_sweep(vertices, faces, freqs_hz,
                              az_deg=0.0, el_deg=0.0,
                              level='full', ram_model=None):
    """RCS vs frequency at a fixed look angle, for a given physics level."""
    rcs = []
    for f in freqs_hz:
        s = make_solver(vertices, faces, f, level=level, ram_model=ram_model)
        rcs.append(s.monostatic_rcs_dbsm(az_deg, el_deg))
    return np.array(rcs)


def breakdown_sweep(vertices, faces, frequency_hz, n=180):
    """
    Full 360° azimuth sweep returning individual contributions.
    Returns dict: key → rcs array (dBsm)
    """
    solver = DoubleBounce(vertices, faces, frequency_hz)
    angles = np.linspace(0, 360, n, endpoint=False)
    keys   = ['PO only', 'PTD edge', 'Double bounce', 'PO + PTD', 'Full (PO+PTD+DB)']
    out    = {k: [] for k in keys}
    for az in angles:
        bd = solver.rcs_breakdown(az)
        for k in keys:
            out[k].append(bd[k])
    out['angles'] = angles
    return {k: np.array(v) if k != 'angles' else v for k, v in out.items()}


def mie_rcs_dbsm(radius_m, frequency_hz):
    """Exact Mie series for conducting sphere (unchanged from v1)."""
    lam   = C_LIGHT / frequency_hz
    ka    = 2.0 * np.pi * radius_m / lam
    n_max = max(int(ka + 4.0*ka**(1/3) + 4), 5)
    S = 0j
    for n in range(1, n_max + 1):
        jn  = spherical_jn(n, ka)
        jnp = spherical_jn(n, ka, derivative=True)
        yn  = spherical_yn(n, ka)
        ynp = spherical_yn(n, ka, derivative=True)
        hn  = jn  + 1j*yn
        hnp = jnp + 1j*ynp
        an  = (ka*jnp + jn)  / (ka*hnp + hn)
        bn  =  jn            /  hn
        S  += (-1)**n * (2*n+1) * (an - bn)
    sigma = (lam**2 / np.pi) * np.abs(S)**2
    return 10.0 * np.log10(sigma + 1e-40)
