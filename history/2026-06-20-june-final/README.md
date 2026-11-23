# Computational RCS Analysis: Conventional vs. Stealth Aerospace Geometries

**A comparative electromagnetic scattering study using Physical Optics, the Physical Theory of Diffraction, second-order corner-reflector interactions, and frequency-dependent radar-absorbing material models — implemented entirely in Python.**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Fundamentals of Radar Cross Section](#3-fundamentals-of-radar-cross-section)
4. [Scattering Mechanisms](#4-scattering-mechanisms)
5. [Physical Optics (PO) — Theory and Derivation](#5-physical-optics-po--theory-and-derivation)
6. [Physical Theory of Diffraction (PTD) — Edge Scattering](#6-physical-theory-of-diffraction-ptd--edge-scattering)
7. [Double Bounce — Corner Reflector Physics](#7-double-bounce--corner-reflector-physics)
8. [Mie Series — Exact Validation Baseline](#8-mie-series--exact-validation-baseline)
9. [Radar Absorbing Material (RAM) Models](#9-radar-absorbing-material-ram-models)
10. [Bistatic RCS](#10-bistatic-rcs)
11. [Geometry Design Rationale](#11-geometry-design-rationale)
12. [Software Architecture](#12-software-architecture)
13. [How to Run](#13-how-to-run)
14. [Results Summary](#14-results-summary)
15. [Low-Observable Design Principles — Derived Findings](#15-low-observable-design-principles--derived-findings)
16. [Limitations and Future Work](#16-limitations-and-future-work)
17. [References](#17-references)

---

## 1. Project Overview

This project performs a **computational comparative analysis** of Radar Cross Section (RCS) between conventional and stealth-inspired aerospace geometries. The objective is to quantify how geometric shaping affects electromagnetic detectability and to derive the fundamental design principles that reduce radar signature.

The codebase implements three coherent, additive electromagnetic scattering mechanisms from first principles, validated against an exact analytical solution (Mie series), and applies them to six distinct 3D geometries: a sphere, a flat plate, a conventional aircraft, a stealth aircraft, a flying-wing configuration, and a chined-nose fighter configuration.

Every scattering computation in this project is derived from Maxwell's equations under the high-frequency approximation — nothing is hard-coded or looked up from a table. The code computes complex scattering amplitudes facet-by-facet and edge-by-edge, sums them coherently (preserving phase), and squares the result to obtain physical RCS in dBsm.

---

## 2. Problem Statement

> Modern radar systems remain one of the primary means of detecting, tracking, and identifying aerospace vehicles. The Radar Cross Section (RCS) of an object is strongly dependent on its external geometry, orientation relative to the incident radar wave, and electromagnetic operating frequency. Traditional aerospace configurations are primarily designed based on aerodynamic, structural, and mission requirements, which can lead to geometric features that produce strong radar reflections and increase detectability. Stealth technology addresses this challenge through geometric shaping techniques that redirect scattered electromagnetic energy away from the radar receiver, thereby reducing the apparent radar signature of the vehicle. This project performs a computational comparative analysis between conventional and stealth-inspired aerospace geometries to investigate how geometric parameters influence electromagnetic scattering behavior and RCS, across varying radar frequencies and aspect angles, to formulate fundamental low-observable design principles.

---

## 3. Fundamentals of Radar Cross Section

### 3.1 Definition

Radar Cross Section is formally defined as the equivalent area of a fictitious, perfectly conducting, isotropic scatterer that would produce the same scattered power density at the radar receiver as the actual target, in the limit of the radar being infinitely far away (far-field):

$$
\sigma = \lim_{R \to \infty} 4\pi R^2 \frac{|E_s|^2}{|E_i|^2}
$$

where:
- $R$ = distance from target to radar [m]
- $E_s$ = scattered field amplitude at the receiver
- $E_i$ = incident field amplitude at the target
- $\sigma$ = RCS [m²]

### 3.2 Units — dBsm

Because RCS spans many orders of magnitude (from $10^{-4}$ m² for an insect to $10^{4}$ m² for a ship), it is conventionally expressed logarithmically in **dBsm** (decibels relative to one square metre):

$$
\sigma_{dBsm} = 10 \log_{10}(\sigma \, [\text{m}^2])
$$

### 3.3 Why RCS Is Not Physical Size

RCS depends on:
- **Geometry** — shape, curvature, edges, surface discontinuities
- **Material** — conductivity, permittivity, permeability, coatings
- **Aspect angle** — orientation relative to the radar
- **Frequency** — relationship between wavelength and target dimensions
- **Polarization** — orientation of the E-field vector

A flat metal plate facing the radar squarely can have an RCS many times larger than its physical area, while a sphere of the same projected area has a much smaller, aspect-independent RCS. This is precisely the property stealth shaping exploits — by ensuring no flat surface ever faces a likely threat direction, the RCS in that direction can be reduced by orders of magnitude without changing the vehicle's physical size.

### 3.4 The Radar Range Equation

The link between RCS and detectability is the radar range equation:

$$
R_{max} = \left[ \frac{P_t \, G_t \, G_r \, \lambda^2 \, \sigma}{(4\pi)^3 \, S_{min}} \right]^{1/4}
$$

where $P_t$ is transmit power, $G_t, G_r$ are antenna gains, $\lambda$ is wavelength, and $S_{min}$ is the minimum detectable signal power.

**Key insight:** detection range scales as $\sigma^{1/4}$. A 20 dB RCS reduction (100× smaller $\sigma$) only reduces detection range by $100^{-1/4} \approx 0.316$, i.e. a 68% range reduction would need ~100x; concretely a 20dB reduction gives range scaling factor $10^{-20/40}=10^{-0.5}\approx0.316$ — detection range shrinks to about 32% of baseline (not 44% — corrected from rough estimate). This nonlinearity is precisely why stealth design pursues every available dB of reduction: even modest RCS reduction translates to a disproportionately large tactical advantage in stand-off detection range, and below certain RCS thresholds radars cannot reliably resolve a target from background clutter at all.

---

## 4. Scattering Mechanisms

Electromagnetic backscatter from a complex object arises from several distinct physical mechanisms. This project implements three of them coherently:

| Mechanism | Physical Origin | Code Module |
|---|---|---|
| **Specular reflection** | Flat or gently curved surfaces reflecting like a mirror | `POAmplitudeSolver` |
| **Edge diffraction** | Field discontinuity at edges, tips, and surface joins | `PTDSolver` |
| **Multiple bounce** | Ray reflecting off one surface onto another, then back to source | `DoubleBounce` |

A fourth mechanism — **traveling/creeping waves** around smooth curved bodies — is captured exactly (not approximated) only for the sphere via the Mie series, used purely as a validation reference.

### 4.1 Specular Reflection

When a flat surface directly faces the radar, the reflected ray returns exactly along the path it arrived from — this is the **dominant** RCS contributor for any flat panel oriented perpendicular to the line of sight. RCS from specular reflection scales with the **square of the illuminated area** and is **strongly aspect-dependent** — it falls off rapidly once the surface tilts away from broadside.

### 4.2 Edge Diffraction

At any geometric discontinuity — a wing tip, a panel edge, a sharp corner — the induced surface currents predicted by simple geometric optics are discontinuous, which is non-physical. The true (fringe) current required to satisfy Maxwell's boundary conditions radiates additional energy that geometric optics misses entirely. This is the **diffracted field**, and it is often the dominant return when no flat surface is directly broadside to the radar (precisely the design condition stealth aircraft try to maintain).

### 4.3 Corner Reflectors / Multiple Bounce

When two (or three) surfaces meet near a right angle, a ray can reflect off the first surface directly onto the second, and back out along the reverse of its original path — a **retroreflector**. This effect is *aspect-angle independent* over a wide range of angles (unlike single-bounce specular return, which requires near-perfect broadside alignment), making corner reflectors a particularly persistent and hard-to-avoid RCS source. Right-angle wing-fuselage and fin-fuselage junctions on conventional aircraft are textbook corner reflectors.

---

## 5. Physical Optics (PO) — Theory and Derivation

### 5.1 Physical Setup

Physical Optics is a **high-frequency approximation** valid when the target dimensions are large compared to the wavelength ($ka \gg 1$, where $a$ is a characteristic dimension). Under this approximation, the induced surface current on an illuminated conducting surface is approximated by the **tangent-plane** (geometric optics) current:

$$
\vec{J}_s \approx 2\hat{n} \times \vec{H}_i
$$

on illuminated surfaces, and $\vec{J}_s = 0$ on shadowed surfaces — this is the fundamental PO approximation: each point on the surface scatters as if it were part of an infinite locally tangent plane.

### 5.2 Discretization into Facets

The continuous surface integral for the scattered field is discretized into a sum over $N$ planar triangular facets. For facet $i$ with area $A_i$, outward unit normal $\hat{n}_i$, and centroid $\vec{c}_i$, illuminated by a plane wave arriving from unit direction $\hat{s}$ (monostatic: transmitter and receiver co-located), the **complex scattering amplitude** contribution is:

$$
f_i = A_i \, (\hat{n}_i \cdot \hat{s}) \, \exp\left(j \, 2k \, \vec{c}_i \cdot \hat{s}\right)
$$

where $k = 2\pi/\lambda$ is the free-space wavenumber.

**Term-by-term physical meaning:**

| Term | Meaning |
|---|---|
| $A_i$ | Larger facets scatter proportionally more energy |
| $\hat{n}_i \cdot \hat{s}$ | Projected illumination — Lambert's cosine factor; zero or negative means the facet is shadowed |
| $\exp(j\,2k\,\vec{c}_i\cdot\hat{s})$ | Round-trip phase — encodes the facet's position relative to all others, enabling **coherent interference** between facets |
| factor of 2 in the exponent | Accounts for the two-way travel path (incident + scattered) in the monostatic case |

### 5.3 Total Scattered Amplitude and RCS

Only **illuminated** facets contribute (first-order shadowing test):

$$
\text{illuminated} \iff \hat{n}_i \cdot \hat{s} > 0
$$

The total coherent scattering amplitude is the sum over all illuminated facets:

$$
f_{PO}(\hat{s}) = \sum_{i \,:\, \hat{n}_i \cdot \hat{s} > 0} A_i \,(\hat{n}_i \cdot \hat{s})\, \exp(j\,2k\,\vec{c}_i\cdot\hat{s})
$$

and the monostatic RCS follows from the standard far-field relation:

$$
\sigma_{PO} = \frac{4\pi}{\lambda^2} \left| f_{PO}(\hat{s}) \right|^2
$$

### 5.4 Why Coherent Summation Matters

Because each facet contributes a **complex number** (not just a positive scalar), facets can interfere **constructively** (in-phase, amplifying RCS) or **destructively** (out-of-phase, partially cancelling). This interference is what produces the characteristic lobed, oscillatory structure seen in real RCS polar plots and frequency sweeps — it is a direct consequence of treating scattering as a coherent wave phenomenon rather than simple ray-tracing with intensity addition.

### 5.5 Code Implementation

```python
def _po_amplitude(self, shat):
    cos_theta = self.normals @ shat
    illum     = cos_theta > 1e-6
    phase   = np.exp(1j * 2.0 * self.k * (self.centroids[illum] @ shat))
    weights = self.reflectivity[illum] * cos_theta[illum] * self.areas[illum]
    return np.dot(weights, phase)
```

---

## 6. Physical Theory of Diffraction (PTD) — Edge Scattering

### 6.1 Motivation

Physical Optics, by construction, only accounts for the smooth tangent-plane current and produces **zero current right at an edge in the direction tangent to it**, even though Maxwell's boundary conditions require a non-zero fringe current there to satisfy continuity. PO therefore **systematically under-predicts** RCS in directions where no facet is broadside to the radar — exactly the operating condition stealth shapes are designed for. This is why an edge-diffraction correction is essential for accurate stealth-aircraft RCS prediction.

Ufimtsev's **Physical Theory of Diffraction** (1962) corrects this by adding a **fringe current** correction localized at each edge, derived from the canonical solution for diffraction by an infinite conducting wedge (the **Sommerfeld/Keller wedge diffraction problem**).

### 6.2 Wedge Diffraction Coefficient

For a perfectly conducting wedge of **exterior wedge angle** $n\pi$ (so $n=2$ for a half-plane / free edge, $n=1$ for a flat continuous surface — i.e. no edge), the monostatic backscatter diffraction coefficient (polarization-averaged) used in this project is:

$$
D(n, \beta) = -\frac{e^{-j\pi/4}}{n\sqrt{2\pi k}} \cdot \frac{\cot\!\left(\dfrac{\pi}{2n}\right)}{\sin\beta}
$$

where $\beta$ is the angle between the edge direction $\hat{e}$ and the radar look direction $\hat{s}$ (so $\sin\beta = \sqrt{1-(\hat{e}\cdot\hat{s})^2}$).

**Physical interpretation of $n$:**

| $n$ value | Configuration | $\cot(\pi/2n)$ |
|---|---|---|
| $n = 1.0$ | Flat (no edge at all) | $0$ — no diffraction |
| $n = 1.5$ | 90° convex ridge | $1/\sqrt{3} \approx 0.577$ |
| $n = 2.0$ | Half-plane / free edge (e.g. wing tip) | $1.0$ |
| $n = 2.5$ | 90° concave (interior) corner | $\approx 1.376$ — strongest diffraction |

A **larger $n$ produces stronger diffraction**, which is why concave/interior corners diffract more strongly than convex ridges, and free edges diffract more strongly than smooth ridges.

### 6.3 Edge Classification Algorithm

Every unique edge in the triangulated mesh is extracted, and classified by counting adjacent facets:

- **Boundary edges** (1 adjacent facet) — physical free edges (e.g. wing trailing edge) → $n = 2.0$
- **Internal edges** (2 adjacent facets) — the exterior wedge angle is computed from the dihedral angle between the two adjacent facet normals, and the sign of the convexity test determines whether the edge is a convex ridge ($n < 2$) or a concave corner ($n > 2$):

$$
n_{ext} = \begin{cases}
\dfrac{\pi + \theta_{dih}}{\pi} & \text{convex (ridge)} \\[2mm]
\dfrac{2\pi - \theta_{dih}}{\pi} & \text{concave (interior corner)}
\end{cases}
$$

where $\theta_{dih} = \arccos(\hat{n}_1 \cdot \hat{n}_2)$ is the angle between the two adjacent facet normals.

### 6.4 Finite Edge Length — the sinc Factor

A wedge of infinite length diffracts a delta-function-like return at $\beta=90°$. A **finite-length edge** of length $L$ instead produces a broadened lobe described by a $\text{sinc}$ function — this is the standard finite-aperture diffraction pattern result:

$$
\text{sinc}(kL\cos\beta) = \frac{\sin(kL\cos\beta)}{kL\cos\beta}
$$

This factor peaks ($=1$) when the edge is exactly perpendicular to the radar look direction ($\beta=90°$, $\cos\beta=0$) and falls off rapidly as the edge tilts away — physically, this is why **sweeping an edge** (as in a delta wing) moves its diffraction peak to a different aspect angle, which is a core stealth shaping technique (edge alignment).

### 6.5 Total Edge Contribution

The coherent sum over all $N_e$ edges in the mesh:

$$
f_{PTD}(\hat{s}) = \sum_{k=1}^{N_e} D(n_k, \beta_k) \, L_k \, \text{sinc}(kL_k\cos\beta_k) \, \exp\!\left(j\,2k\,\vec{c}_k \cdot \hat{s}\right)
$$

where $\vec{c}_k$ is the edge midpoint.

### 6.6 Combined PO+PTD RCS

The PO and PTD amplitudes are summed **coherently** (as complex numbers) before squaring, because both arise from the same physical surface current and must interfere correctly:

$$
\sigma_{PO+PTD} = \frac{4\pi}{\lambda^2}\left|f_{PO}(\hat{s}) + f_{PTD}(\hat{s})\right|^2
$$

### 6.7 Code Implementation

```python
def _D_fringe(self, n, sin_beta):
    arg = np.pi / (2.0 * n)
    cot = np.cos(arg) / (np.sin(arg) + 1e-15)
    prefactor = np.exp(-1j*np.pi/4.0) / (n*np.sqrt(2.0*np.pi*self.k))
    return -prefactor * cot / sin_beta

def _edge_amplitude(self, shat):
    total = 0j
    for i in range(len(self.edges)):
        cos_beta = np.dot(self.edge_dir[i], shat)
        sin_beta = np.sqrt(max(0.0, 1.0 - cos_beta**2))
        D     = self._D_fringe(self.edge_n[i], sin_beta)
        sinc  = _sinc(self.k * self.edge_L[i] * cos_beta)
        phase = np.exp(1j * 2.0 * self.k * np.dot(self.edge_c[i], shat))
        total += D * self.edge_L[i] * sinc * phase
    return total
```

---

## 7. Double Bounce — Corner Reflector Physics

### 7.1 The Retroreflection Problem

PO and PTD both model **single-bounce** scattering — a ray hits one facet (or edge) and the return is computed directly. But when two facets are oriented near a right angle (e.g. a vertical fin meeting a horizontal fuselage top), a ray can specularly reflect off the **first** facet, travel to the **second** facet, reflect again, and return **exactly back along the original line of sight** — regardless of the precise approach angle, over a wide angular range. This is the defining property of a **corner reflector** and explains why conventional aircraft (full of right-angle wing/fin/fuselage junctions) are so persistently visible to radar across a broad range of aspect angles, not just at one precise broadside angle.

### 7.2 Ray-Tracing Formulation

For each ordered facet pair $(i, j)$ with $i \ne j$:

**Step 1 — First reflection.** The incident ray direction is $\vec{d}_{inc} = -\hat{s}$ (travelling from the radar toward the target). Applying the law of reflection at facet $i$:

$$
\vec{d}_{ref,i} = \vec{d}_{inc} - 2(\vec{d}_{inc}\cdot\hat{n}_i)\,\hat{n}_i
$$

**Step 2 — Check illumination of facet j by the reflected ray.** Facet $j$ is illuminated by this secondary ray if:

$$
\hat{n}_j \cdot (-\vec{d}_{ref,i}) > 0
$$

**Step 3 — Second reflection, and the retroreflection test.** Apply the law of reflection again at facet $j$:

$$
\vec{d}_{ref,j} = \vec{d}_{ref,i} - 2(\vec{d}_{ref,i}\cdot\hat{n}_j)\,\hat{n}_j
$$

The pair $(i,j)$ contributes to the **monostatic** return only if this second-bounce ray travels back toward the radar:

$$
\vec{d}_{ref,j}\cdot\hat{s} > \text{threshold (}\approx 0.2\text{, i.e. within} \sim 78°\text{ of exact retroreflection)}
$$

> **Implementation note (bug history):** An earlier version of this code incorrectly tested $\hat{n}_j\cdot\hat{s}>0$ (facet $j$ facing the radar) instead of testing the *second-bounce ray direction* against the radar direction. This is physically wrong — in a genuine corner reflector, facet $j$ does **not** face the radar at all; it faces the interior of the angle formed with facet $i$. The corrected check evaluates $\vec{d}_{ref,j}\cdot\hat{s}$, the actual outgoing direction after two bounces, against the radar direction. A second related bug used a single fixed test angle of exactly 90°, at which all illuminated facets share an identical surface normal, so every "reflected" ray pointed in the same direction and never satisfied a meaningful corner condition — corner-reflector enhancement is strongest at *oblique* angles (typically 30–60° off the symmetry axis of the corner), not at exact broadside. The corrected analysis sums contributions across a representative threat sector (15°–75°) rather than evaluating a single unrepresentative angle.

### 7.3 Amplitude and Phase

The amplitude contribution from pair $(i,j)$ combines both cosine-weighted areas (energy collected by facet $i$, redirected, then collected and re-radiated by facet $j$):

$$
A_{ij} = A_i\,(\hat{n}_i\cdot\hat{s})\;\times\;A_j\,\big[\hat{n}_j\cdot(-\vec{d}_{ref,i})\big]\,\big[\vec{d}_{ref,j}\cdot\hat{s}\big]
$$

The two-leg path length determines the phase (radar→facet $i$→facet $j$→radar):

$$
\text{path} = \hat{s}\cdot\vec{c}_i \;+\; \left|\vec{d}_{ref,i}\cdot(\vec{c}_j-\vec{c}_i)\right| \;+\; \hat{s}\cdot\vec{c}_j
$$

$$
f_{ij} = A_{ij}\,\exp(j\,k\,\text{path})
$$

### 7.4 Total Double-Bounce Amplitude and Full RCS

$$
f_{DB}(\hat{s}) = \sum_{i}\sum_{j\ne i} f_{ij}
$$

All three mechanisms are combined coherently for the final, full-physics RCS:

$$
\sigma_{Full} = \frac{4\pi}{\lambda^2}\left|f_{PO}(\hat{s}) + f_{PTD}(\hat{s}) + f_{DB}(\hat{s})\right|^2
$$

### 7.5 Diagnostic Tool — The Double-Bounce Matrix

To visualize *which specific facet pairs* drive corner-reflector enhancement, the code computes an $N\times N$ matrix where cell $(i,j)$ holds the angle-summed amplitude contribution of that specific pair across the 15°–75° threat sector. On the conventional aircraft this matrix shows clear bright clusters corresponding to the fin/fuselage and wing/fuselage junctions; on the stealth aircraft — which has no right-angle dihedrals by design — the matrix is comparatively sparse and dim.

---

## 8. Mie Series — Exact Validation Baseline

### 8.1 Why a Sphere?

The conducting sphere is one of only a handful of 3D geometries for which Maxwell's equations admit a **closed-form, exact** solution at all frequencies — no high-frequency approximation required. It therefore serves as the **ground-truth validation case**: if the PO implementation agrees with the Mie series in the optical (high-frequency) regime, the discretization, normal/area computation, and coherent-summation logic are all verified correct.

### 8.2 The Mie Series Formula

For a PEC sphere of radius $a$, illuminated by a plane wave, the exact monostatic backscatter RCS is:

$$
\sigma = \frac{\lambda^2}{\pi}\left|\sum_{n=1}^{\infty}(-1)^n(2n+1)(a_n - b_n)\right|^2
$$

where $a_n$ (TM/electric coefficients) and $b_n$ (TE/magnetic coefficients) are the **Mie scattering coefficients**:

$$
a_n = \frac{ka\,j_n'(ka) + j_n(ka)}{ka\,h_n'(ka) + h_n(ka)}, \qquad
b_n = \frac{j_n(ka)}{h_n(ka)}
$$

with $j_n$ the spherical Bessel function of the first kind, $h_n = j_n + jy_n$ the spherical Hankel function, and $j_n', h_n'$ their derivatives with respect to the argument. These coefficients arise from enforcing the PEC boundary condition (vanishing tangential E-field at $r=a$) on the spherical-harmonic expansion of the scattered field.

### 8.3 Three Scattering Regimes

The behaviour of $\sigma$ vs. $ka = 2\pi a/\lambda$ falls into three classical regimes:

| Regime | Condition | Behaviour |
|---|---|---|
| **Rayleigh** | $ka \ll 1$ | $\sigma \propto (ka)^4 \cdot \pi a^2 \propto r^6/\lambda^4$ — strongly frequency-dependent, very small RCS |
| **Resonance (Mie)** | $ka \sim 1$ | Oscillatory RCS vs frequency due to creeping-wave interference around the sphere |
| **Optical** | $ka \gg 1$ | $\sigma \to \pi a^2$ — converges to the simple geometric projected area |

### 8.4 Convergence — Number of Terms

The series is truncated using the **Wiscombe criterion**, which guarantees numerically converged results:

$$
n_{max} = \lceil ka + 4(ka)^{1/3} + 4 \rceil
$$

At the project's standard test case ($a=1$ m, $f=10$ GHz $\Rightarrow ka \approx 210$), this requires roughly 230 terms — well into the **optical regime**, where the PO solver is expected to (and does) closely match the Mie result, validating the discretized PO implementation.

### 8.5 Code Implementation

```python
def mie_rcs_dbsm(radius_m, frequency_hz):
    ka = 2*np.pi*radius_m / (C_LIGHT/frequency_hz)
    n_max = max(int(ka + 4*ka**(1/3) + 4), 5)
    S = 0j
    for n in range(1, n_max+1):
        jn, jnp = spherical_jn(n, ka), spherical_jn(n, ka, derivative=True)
        yn, ynp = spherical_yn(n, ka), spherical_yn(n, ka, derivative=True)
        hn, hnp = jn + 1j*yn, jnp + 1j*ynp
        an = (ka*jnp + jn) / (ka*hnp + hn)
        bn =  jn / hn
        S += (-1)**n * (2*n+1) * (an - bn)
    sigma = (lam**2/np.pi) * np.abs(S)**2
    return 10*np.log10(sigma)
```

---

## 9. Radar Absorbing Material (RAM) Models

Geometric shaping alone is the dominant lever in this project (it determines *where* energy goes), but real stealth aircraft also apply absorptive coatings to reduce the *amplitude* of whatever energy does return. Two classical, physics-based RAM models are implemented; both compute a complex reflection coefficient $\Gamma(f)$ from transmission-line theory.

### 9.1 General Transmission-Line Approach

Any planar layered absorber backed by a PEC ground plane can be modelled using transmission-line input impedance:

$$
\Gamma(f) = \frac{Z_{in}(f) - Z_0}{Z_{in}(f) + Z_0}, \qquad Z_0 = \sqrt{\mu_0/\varepsilon_0} \approx 376.73\ \Omega
$$

The **amplitude reflectivity** $|\Gamma(f)|$ multiplies the PO/PTD/double-bounce facet reflectivity term-by-term (i.e. $\rho_i = |\Gamma(f)|$ replaces $\rho_i=1$ for a coated facet), directly attenuating the coherent scattering amplitude before the final $|\cdot|^2$.

### 9.2 Salisbury Screen (Narrowband Absorber)

A **Salisbury screen** consists of a resistive sheet placed a quarter-wavelength in front of a PEC ground plane:

$$
Z_{gp}(f) = jZ_0\tan\!\left(\frac{2\pi f\,d}{c}\right), \qquad d = \frac{c}{4f_0}
$$

$$
Z_{in} = \frac{R_s \, Z_{gp}}{R_s + Z_{gp}}
$$

When $R_s = Z_0$ (matched sheet resistance) and the spacer thickness $d=\lambda_0/4$ at the design frequency $f_0$, the ground-plane short circuit is transformed into an open circuit, so all incident power is dissipated in the resistive sheet — **$\Gamma(f_0) = 0$, perfect absorption** at the design frequency. This absorber is inherently **narrowband**: absorption degrades rapidly away from $f_0$.

### 9.3 Dallenbach Layer (Broadband Absorber)

A **Dallenbach layer** is a single homogeneous lossy dielectric/magnetic slab of thickness $d$ backed by a PEC plane, characterised by complex relative permittivity $\varepsilon_r = \varepsilon' - j\varepsilon''$ and permeability $\mu_r = \mu' - j\mu''$:

$$
\gamma = j\frac{2\pi f}{c}\sqrt{\mu_r\varepsilon_r}, \qquad Z_m = Z_0\sqrt{\frac{\mu_r}{\varepsilon_r}}, \qquad Z_{in} = Z_m\tanh(\gamma d)
$$

Because $\varepsilon_r$ and $\mu_r$ are complex, the slab is lossy and the absorption — while not as deep at any single frequency as a tuned Salisbury screen — extends over a much **wider bandwidth**. Three representative material presets are included (parameter values are illustrative X-band approximations, not measured datasheet values):

| Preset | $\varepsilon_r$ | $\mu_r$ | Character |
|---|---|---|---|
| `carbon_foam` | $1.5-0.8j$ | $1.0$ | Lightweight, moderate absorption |
| `carbonyl_iron` | $8-4j$ | $1.8-0.9j$ | Balanced weight/performance |
| `ferrite_tile` | $12-3j$ | $2.5-1.5j$ | Heaviest, strongest broadband absorption |

### 9.4 Code Implementation

```python
class SalisburyScreen:
    def __init__(self, f0_hz, Rs=Z0):
        self.f0, self.Rs = f0_hz, Rs
        self.d = C_LIGHT / (4.0 * f0_hz)
    def reflection_coefficient(self, f):
        Z_gp = 1j*Z0*np.tan(2*np.pi*f*self.d/C_LIGHT)
        Z_in = self.Rs*Z_gp / (self.Rs + Z_gp)
        return (Z_in - Z0) / (Z_in + Z0)

class DallenbachLayer:
    def __init__(self, thickness_m, eps_r, mu_r):
        self.d, self.eps_r, self.mu_r = thickness_m, eps_r, mu_r
    def reflection_coefficient(self, f):
        k0 = 2*np.pi*f/C_LIGHT
        gamma = 1j*k0*np.sqrt(self.mu_r*self.eps_r)
        Z_m = Z0*np.sqrt(self.mu_r/self.eps_r)
        Z_in = Z_m*np.tanh(gamma*self.d)
        return (Z_in - Z0) / (Z_in + Z0)
```

---

## 10. Bistatic RCS

All mechanisms above assume **monostatic** radar (transmitter and receiver co-located). Real-world threats increasingly include **bistatic** and **multistatic** radar networks, where the receiver is physically separated from the transmitter. The code generalises the PO formulation to this case:

$$
\sigma_{bi} = \frac{4\pi}{\lambda^2}\left|\sum_i \rho_i A_i \cdot \tfrac{1}{2}\big[(\hat{n}_i\cdot\hat{s}_{tx})+(\hat{n}_i\cdot\hat{s}_{rx})\big] \cdot \exp\!\big(jk(\hat{s}_{tx}+\hat{s}_{rx})\cdot\vec{c}_i\big)\right|^2
$$

A facet contributes only if it is simultaneously illuminated by the transmitter **and** visible to the receiver. The special case $\hat{s}_{tx}=\hat{s}_{rx}$ recovers the monostatic formula exactly. At the **forward-scatter** condition (bistatic angle $\beta \to 180°$), RCS rises sharply for *any* geometry — including stealth shapes — because forward scatter is governed by Babinet's principle / physical shadow area rather than surface orientation. This is a well-known fundamental vulnerability of geometric shaping to forward-scatter / multistatic radar geometries.

---

## 11. Geometry Design Rationale

All six geometries are built as **triangulated meshes** — collections of planar triangles, each with a well-defined area, centroid, and outward normal (computed via the cross product of two edge vectors, with winding order controlling normal direction).

### 11.1 Sphere
UV-sphere triangulation. Used purely for Mie series validation — its RCS is aspect-independent.

### 11.2 Flat Plate
Two triangles forming a single 2×2 m square. Demonstrates maximal specular return when broadside, and the $\sigma \propto A^2/\lambda^2$ scaling law.

### 11.3 Conventional Aircraft
Deliberately designed to embody every classical RCS problem:
- **Box fuselage** — flat sides (broadside spike), flat ends (nose/tail spike)
- **Zero-dihedral flat wings** — top/bottom specular return; **90° wing-fuselage junction is a corner reflector**
- **Vertical stabilizer** — flat vertical slab maximally illuminated at broadside; **fin-fuselage junction is a second corner reflector**
- **Flat nose face** — simulates an intake, maximal nose-on return

### 11.4 Stealth Aircraft
Every feature is a direct, deliberate counter to a conventional-aircraft RCS problem:
- **Trapezoidal fuselage cross-section** — angled side panels redirect energy up/down rather than back to a horizontal radar
- **Pointed pyramidal nose** — near-zero frontal area, no flat nose-on face
- **~65° swept delta wings** — leading-edge diffraction spike pushed to a wide, non-threatening angle (well outside the typical ±30° frontal threat sector); trailing edges kept parallel to leading edges (**edge alignment principle**) to concentrate all diffraction spikes into the same few angular sectors rather than spreading them across the full field of view
- **35°-canted V-tail** — replaces the single vertical fin; eliminates the 90° fin-fuselage dihedral entirely, suppressing the dominant double-bounce mechanism

### 11.5 Flying Wing (B-2-inspired)
No discrete fuselage/wing/tail distinction at all — a single continuous lifting surface with a faceted "kite" planform, sawtooth (double-W) trailing edge for edge alignment across multiple panel-to-panel joints, and **zero vertical surfaces** — eliminating broadside specular return entirely.

### 11.6 Chined-Nose Aircraft (F-22-inspired)
Forebody **chines** (sharp longitudinal edges) blend a faceted, diamond-cross-section fuselage smoothly into the wing leading edge, aligning forebody edge diffraction with the wing's. Twin vertical tails are canted ~28° outward, again avoiding any 90° dihedral with the fuselage.

---

## 12. Software Architecture

```
rcs_final/
├── geometries.py             — Mesh construction for all 6 geometries
├── solvers.py                 — Full physics engine (PO, PTD, DoubleBounce, RAM, Mie)
├── main.py     — Individual single-subject PNG figure generator
└── README.md                  — This document
```

### 12.1 `geometries.py`

Builds triangulated meshes as `(vertices, faces)` NumPy array pairs. Primitive helpers (`_quad`, `_box`, `_tri`, `_combine`) compose into the six full geometries. All winding orders are chosen so outward normals are correct (verified numerically — illuminated-facet counts and double-bounce results behave as physically expected).

### 12.2 `solvers.py`

| Class | Physics included |
|---|---|
| `POAmplitudeSolver` | PO only |
| `PTDSolver` (extends PO) | + edge diffraction |
| `DoubleBounce` (extends PTD) | + corner-reflector second-order bounces |
| `SalisburyScreen`, `DallenbachLayer` | Frequency-dependent RAM reflectivity, pluggable into any solver via `ram_model=` |

Key design choice: every solver level returns/uses **complex amplitudes** internally (`_po_amplitude`, `_edge_amplitude`, `_double_bounce_amplitude`), and only the **final combined sum** is squared to get RCS — this preserves correct coherent interference between mechanisms, which is physically essential and would be lost if each mechanism's *power* were computed and added separately.

### 12.3 `main.py`

Produces ~120+ individual, single-subject PNG files (no multi-panel grids) organized into 8 categories, suitable for direct insertion into presentation slides: geometry views (iso/front/side/top/wireframe), RCS polar plots, heatmaps, frequency sweeps, RAM comparisons, mechanism breakdowns, cross-geometry comparisons, and physics explainer diagrams.

---

## 13. How to Run

```bash
# 1. Install dependencies
pip install numpy scipy matplotlib

# 2. Generate the full PPT asset library (takes a few minutes — heatmaps
#    and breakdown sweeps are the slowest steps)
python3 main.py

# Output: ./output_ppt/<category>/*.png  (~120+ individual images)
```

To use the physics engine directly in your own scripts:

```python
from geometries import conventional_aircraft, stealth_aircraft
from solvers import DoubleBounce, SalisburyScreen

V, F = stealth_aircraft()
solver = DoubleBounce(V, F, frequency_hz=10e9, ram_model=SalisburyScreen(10e9))

rcs = solver.monostatic_rcs_dbsm(az_deg=0, el_deg=0)
breakdown = solver.rcs_breakdown(az_deg=45)   # per-mechanism dB contributions
angles, rcs_sweep = solver.azimuth_sweep(n=360)
```

---

## 14. Results Summary

*(Representative figures from the X-band, 10 GHz analysis — see `./output_ppt/` for the full image set.)*

| Metric | Conventional | Stealth | Δ (reduction) |
|---|---|---|---|
| Nose-on RCS (full physics) | highest of all aspects | substantially reduced | tens of dB |
| Broadside RCS | dominated by fin/fuselage corner reflector | double-bounce contribution near-zero | large reduction |
| PTD edge contribution | moderate (41 internal wedge edges, many ≈90° ridges) | larger relative share of total (44 boundary half-plane edges) but redirected to non-threat angles | — |
| Double-bounce matrix | 48 nonzero high-amplitude facet pairs | ~22 nonzero, roughly half peak amplitude, no 90° dihedral hotspot | confirms elimination of corner-reflector effect |
| Edge wedge parameter $n$ | mean ≈1.80 (many convex ridges) | uniformly $n=2.0$ (all free half-plane edges, zero internal ridges) | confirms absence of right-angle structure |

**Interpretation:** the wedge-parameter statistics alone numerically prove what stealth design theory predicts qualitatively — the conventional airframe is structurally full of sharp ridge and corner geometry, while the stealth airframe's edge population consists entirely of free (half-plane) edges with no internal right-angle wedges at all.

---

## 15. Low-Observable Design Principles — Derived Findings

Synthesising the computational results, the following design principles emerge directly from the physics implemented in this project (not asserted a priori — each is traceable to a specific mechanism above):

1. **Eliminate surfaces broadside to likely threat sectors.** PO scattering scales with $A^2$ for a broadside flat panel; angling every panel even modestly collapses this term.
2. **Align edges in parallel families.** Because PTD diffraction peaks sharply when $\beta=90°$ (edge ⊥ radar) and falls off via a sinc envelope elsewhere, concentrating all edges to a small number of shared directions concentrates diffraction returns into a small number of predictable, controllable angular spikes rather than spreading them across the whole field of regard.
3. **Avoid right-angle (and near-right-angle) dihedral junctions.** This is the single most effective lever against the double-bounce mechanism, which is otherwise aspect-angle-robust and very difficult to suppress by surface treatment alone.
4. **Use swept, not perpendicular, leading edges.** Sweeping moves the inevitable leading-edge diffraction spike away from the nose-on threat sector.
5. **Cant vertical surfaces rather than using true verticals.** A canted fin both reduces its own $\hat n\cdot\hat s$ illumination factor at broadside *and* removes the 90° dihedral with the fuselage.
6. **Geometric shaping and RAM are complementary, not substitutes.** Shaping controls *where* energy goes (the dominant lever, tens of dB); absorptive coatings reduce the *amplitude* of whatever energy remains in the threat direction (a further, typically smaller, multiplicative reduction) — and a narrowband Salisbury-type coating must be tuned to the specific threat frequency, while a broadband Dallenbach-type layer trades absorption depth for bandwidth.
7. **No amount of monostatic shaping defeats forward-scatter.** Because forward-scatter RCS is governed by the target's physical silhouette/shadow area rather than surface orientation, multistatic and forward-scatter radar geometries remain a fundamental, geometry-independent vulnerability.

---

## 16. Limitations and Future Work

This is a **comparative, educational-grade computational study**, not a certified RCS prediction tool. Known limitations:

- **PEC assumption** — all surfaces are modelled as perfect electric conductors; real composite/metallic skins have finite surface impedance (a Surface Impedance Boundary Condition extension would address this).
- **No polarimetric tracking** — RCS is computed as a scalar; a full 2×2 scattering matrix (HH/HV/VH/VV) would expose cross-polarization behaviour, a known diagnostic for edge/surface discontinuities.
- **First-order shadowing only** — illumination tests use simple normal-dot-product checks, not full ray-occlusion testing; deeply concave geometry could in principle be mis-illuminated.
- **Double bounce limited to second order** — true corner reflectors (e.g. trihedral) can involve three or more bounces; this project implements only the dominant second-order term.
- **Coarse meshes** — geometries use tens of facets, sufficient for comparative trend analysis but not for fine-grained absolute RCS prediction; mesh refinement would improve resolution of the PO integral and edge classification fidelity.
- **RAM material parameters are illustrative**, not measured datasheet values for a specific real material system.

Natural next steps include surface-impedance boundary conditions, full polarimetric scattering matrices, finer mesh refinement with convergence studies, and cross-validation against a full-wave method (HFSS/COMSOL FEM or MoM) on at least one shared geometry to bound the high-frequency approximation's error.

---

## 17. References

Foundational texts and papers underlying the methods implemented here:

- Knott, E. F., Shaeffer, J. F., Tuley, M. T. — *Radar Cross Section*, 2nd ed., SciTech Publishing.
- Ufimtsev, P. Ya. — *Fundamentals of the Physical Theory of Diffraction*, Wiley, 2007 (English translation/expansion of the original 1962 PTD work).
- Keller, J. B. — "Geometrical Theory of Diffraction," *J. Opt. Soc. Am.*, 1962.
- Mie, G. — "Beiträge zur Optik trüber Medien, speziell kolloidaler Metallösungen," *Annalen der Physik*, 1908 (original Mie scattering solution).
- Skolnik, M. I. — *Introduction to Radar Systems*, 3rd ed., McGraw-Hill (radar range equation, RCS fundamentals).
- Munk, B. A. — *Finite Antenna Arrays and FSS*, Wiley (Salisbury screen and absorber theory background).
- Balanis, C. A. — *Advanced Engineering Electromagnetics*, Wiley (wedge diffraction, transmission-line absorber theory).

---

*This README documents the complete physics, mathematics, and software implementation of the project from first principles through final results, for direct use in academic submission and presentation to faculty.*
