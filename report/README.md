# Report, slides and poster

| File | What it is |
|---|---|
| [`rcs-report-official-2026-07-17.pdf`](rcs-report-official-2026-07-17.pdf) | The final report, 66 pages: *Numerical Modeling of Electromagnetic Scattering for Radar Cross Section Prediction: A Computational Comparison of Conventional and Stealth Aircraft Geometries.* Covers the June program and the July extensions. |
| [`slides.pdf`](slides.pdf) | The presentation, 17 July 2026. The team-details page, which listed our email addresses, has been taken out. |
| [`poster.pdf`](poster.pdf) | The poster, 17 July 2026. |
| [`rcs-report-draft-2026-06-23.pdf`](rcs-report-draft-2026-06-23.pdf) | Uday's first write-up of the June program, 23 June 2026. |

These are kept exactly as they were handed in, mistakes included. The list below is what we found
wrong in November 2026; the main [README](../README.md#what-we-checked-in-november-2026) has the detail
and [`rcs/validate.py`](../rcs/validate.py) reproduces the checks.

## Errata

1. **"The Physical Optics solver is validated against the exact Mie series ... matching to within
   0.2 dBsm"** (report abstract, slides, poster flowchart; the June draft says both give 4.97 dBsm).
   The code never did this. Its Mie series was 4 times too large (10.99 dBsm for the 1 m sphere at
   10 GHz instead of πa² = 4.97 dBsm), and PO on the 2,304-facet sphere gave 11.5 to 27.3 dBsm.

2. **"An 11.9 dB RCS reduction over the conventional aircraft at the nose-on aspect, equivalent to a
   radar detection-range reduction from 200 km to 100 km"** (report abstract, slides). At azimuth 0 the
   program put the radar behind the conventional aircraft's tail, and also counted a second, inward-facing
   copy of its flat nose face; for the stealth aircraft, whose facets mostly faced inwards, the same
   setting showed the nose. Every facet was also treated as a point. The number is not supported. With
   the corrections, PO alone gives 40.5 dBsm nose-on for the conventional aircraft and −18.1 dBsm for the
   stealth aircraft, but the stealth aircraft's nose-on return then depends on edge terms this model
   handles only roughly, so there is no corrected number to put in its place.

3. **Every aircraft RCS value** (polar plots, heatmaps, frequency sweeps, absorbers, the summary table,
   and all the July studies) was computed with facets as points and with the mixed facet orientation.
   For the conventional and chined-nose aircraft, what the figures call nose-on is the view from behind,
   and tail-on is the view from the front. The values of 40 to 60 dBsm come from flat facets metres
   across; they describe those boxes, not a real aircraft.

4. **Corner reflectors and double bounce.** The double-bounce term counted pairs of facets that cannot
   send a ray to each other. With that fixed, the conventional, stealth and flying-wing aircraft have no
   double bounce at all at 0° elevation, so the corner returns in our results came from bounces that
   cannot happen (at 45°, most of the conventional aircraft's 59.9 dBsm). The term's size is also wrong:
   it grows with the product of two facet areas.

5. **Mesh convergence** (report chapter 4, poster). The convergence studies were run with facets as
   points, which is why the answers moved by more than 20 dB as the meshes were refined. The stealth
   aircraft's nose-on curve settled on a wrong value, because subdivision never splits its four nose
   triangles.

6. **The edge-diffraction term** adds an amplitude in m<sup>1.5</sup> to the facets' m², so its weight
   against Physical Optics depends on the units and the frequency.

7. The June draft says "Semester VIII". It was the 6th semester.
