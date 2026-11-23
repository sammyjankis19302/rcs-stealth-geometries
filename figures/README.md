# Figures

Every figure in the repository, with what it shows. The [June](#june) and [July](#july) figures are
exactly as the program made them then, with the June model: facets treated as points, the mixed facet
orientation, and azimuth 0 called nose-on even where the radar was behind the aircraft (the
[errata](../report/README.md#errata) explain). The [November](#november) figures come from the corrected
solver, from [`rcs/validate.py`](../rcs/validate.py) and [`tools/make_figures.py`](../tools/make_figures.py).

- [November](#november) · [Explained](#explained) · [Report, slides and poster](#report-slides-and-poster)
  · [June](#june) · [The first tries, 12 to 19 June](#the-first-tries-12-to-19-june) · [July](#july)

## November

| | |
|---|---|
| [`radar-sweep.gif`](november/radar-sweep.gif) | The radar goes once round the conventional and stealth aircraft, and the echo is drawn as it goes. Physical Optics, 10 GHz, corrected solver. |
| [`validation.png`](november/validation.png) | The checks against exact answers: a 2 m flat plate against the textbook formula, a 1 m sphere against the Mie series, and the conventional aircraft's facets cut finer and finer at 1 GHz. Each with facets as points (June) and integrated exactly (November). |
| [`corrected-po-comparison.png`](november/corrected-po-comparison.png) | The four aircraft round the azimuth circle with the corrected Physical Optics, with the nose-on, broadside and tail-on values. Edges and corners not included. |
| [`then-and-now.png`](november/then-and-now.png) | June as presented (gray) against November corrected (colour), as polar plots for all four aircraft. The June curves come from running the June code in [`history/2026-06-20-june-final`](../history/2026-06-20-june-final). |

## Explained

| | |
|---|---|
| [`what-rcs-is.png`](explained/what-rcs-is.png) | The radar, the pulse and the echo; what σ and dBsm mean, with numbers from this project; and how detection range falls as the RCS is cut (range ∝ σ<sup>¼</sup>). |
| [`why-shape-matters.png`](explained/why-shape-matters.png) | A flat face square-on and tilted, and the computed echo of a 2 m plate as it tilts: 53.5 dBsm square-on, 21.6 dBsm at 5°, against a 1 m sphere's 4.97 dBsm. |
| [`three-views.png`](explained/three-views.png) | Top, side and front views of the four aircraft, all at the same scale. The stealth aircraft's wings sweep forward. |
| [`timeline.png`](timeline.png) | How the project grew, from 12 June to 24 November 2026. |

## Report, slides and poster

| | |
|---|---|
| [`poster.png`](presentation/poster.png) | The poster, 17 July 2026 ([PDF](../report/poster.pdf)). |
| [`slides.png`](presentation/slides.png) | Eight of the slides: title, project overview, methodology, the shapes, the conventional aircraft, the reduction chart, the frequency sweep and the conclusion ([PDF](../report/slides.pdf)). |

## June

The program's figures from 20 June 2026, a selection of its 64.

| | |
|---|---|
| [`geometries.png`](june/geometries.png) | The four aircraft in 3-D. |
| [`polar-conventional.png`](june/polar-conventional.png) | Conventional aircraft, full model (PO, edges and double bounce), 10 GHz. |
| [`polar-stealth.png`](june/polar-stealth.png) | Stealth aircraft, full model. The radial scale runs down to −400 dBsm, the program's value for "no echo", which squashes the curve against the rim. |
| [`polar-flying-wing.png`](june/polar-flying-wing.png) | Flying wing, full model. |
| [`polar-chined-nose.png`](june/polar-chined-nose.png) | Chined-nose aircraft, full model. |
| [`polar-all-shapes.png`](june/polar-all-shapes.png) | All six shapes overlaid; again squashed by the −400 dBsm floor. |
| [`sphere-mie.png`](june/sphere-mie.png) | The 1 m sphere from the Mie series: 10.99 dBsm, the value that turned out 4 times too large (it should be 4.97). |
| [`flat-plate.png`](june/flat-plate.png) | The 2 m flat plate at 0° elevation, where it is seen edge-on and PO gives no echo (−400 dBsm). |
| [`heatmap-conventional.png`](june/heatmap-conventional.png), [`heatmap-stealth.png`](june/heatmap-stealth.png) | RCS over every azimuth and elevation, 10 GHz. |
| [`frequency-conventional-nose.png`](june/frequency-conventional-nose.png), [`frequency-conventional-broadside.png`](june/frequency-conventional-broadside.png), [`frequency-stealth-nose.png`](june/frequency-stealth-nose.png), [`frequency-stealth-broadside.png`](june/frequency-stealth-broadside.png) | RCS from 1 to 36 GHz, nose-on and broadside. |
| [`ram-absorption.png`](june/ram-absorption.png) | How much a Salisbury screen and three Dallenbach layers absorb, against frequency. |
| [`salisbury-screen.png`](june/salisbury-screen.png), [`dallenbach-layer.png`](june/dallenbach-layer.png) | The two absorbers as diagrams: a resistive sheet a quarter-wavelength above the metal, and a lossy layer on the metal. |
| [`stealth-with-salisbury-screen.png`](june/stealth-with-salisbury-screen.png), [`stealth-with-dallenbach-layer.png`](june/stealth-with-dallenbach-layer.png) | The stealth aircraft nose-on, bare and with each absorber, against frequency. |
| [`mechanism-conventional-edges.png`](june/mechanism-conventional-edges.png) | The edge-diffraction part of the conventional aircraft's echo against the total. |
| [`mechanism-stealth-double-bounce.png`](june/mechanism-stealth-double-bounce.png) | The double-bounce part of the stealth aircraft's echo; with the November fix this disappears at 0° elevation. |
| [`edges-conventional.png`](june/edges-conventional.png), [`edges-stealth.png`](june/edges-stealth.png) | How the program classified each aircraft's edges by wedge angle. |
| [`reduction-conventional-to-stealth.png`](june/reduction-conventional-to-stealth.png) | The headline chart: the stealth aircraft's echo below the conventional one at four angles, 11.9 dB nose-on. Not supported, see the errata. |
| [`ranking.png`](june/ranking.png) | Mean RCS of the six shapes (the flat plate's −400 dBsm is its no-echo value at 0° elevation). |

## The first tries, 12 to 19 June

| | |
|---|---|
| [`2026-06-12-first-shapes.png`](june/first-tries/2026-06-12-first-shapes.png) | The first two aircraft from three sides, 12 June, 4:49 am. |
| [`2026-06-12-first-polar-plots.png`](june/first-tries/2026-06-12-first-polar-plots.png) | The first RCS polar plots: the sphere, the plate and the two aircraft. |
| [`2026-06-12-first-frequency-sweep.png`](june/first-tries/2026-06-12-first-frequency-sweep.png) | The first frequency sweep, 1 to 36 GHz. |
| [`2026-06-12-first-heatmaps.png`](june/first-tries/2026-06-12-first-heatmaps.png) | The first azimuth-elevation heatmaps. |
| [`2026-06-12-first-summary.png`](june/first-tries/2026-06-12-first-summary.png) | The first summary page, with the design principles. |
| [`2026-06-14-six-shapes.png`](june/first-tries/2026-06-14-six-shapes.png) | Six shapes: the flying wing and the chined-nose aircraft join, 14 June. |
| [`2026-06-14-first-animation.gif`](june/first-tries/2026-06-14-first-animation.gif) | The first animation: the two aircraft turning in front of the radar, 14 June, 1:31 am. |
| [`2026-06-14-bistatic.png`](june/first-tries/2026-06-14-bistatic.png) | The first bistatic sweeps, with the receiver away from the transmitter. |
| [`2026-06-14-absorber-coating.png`](june/first-tries/2026-06-14-absorber-coating.png) | Generic absorber coatings of 5, 10 and 20 dB on both aircraft, nose-on. |
| [`2026-06-14-all-shapes-compared.png`](june/first-tries/2026-06-14-all-shapes-compared.png) | All six shapes overlaid, with a ranking by mean RCS. |
| [`2026-06-14-physics-levels.png`](june/first-tries/2026-06-14-physics-levels.png) | PO alone, PO with edges, and PO with edges and double bounce. |
| [`2026-06-14-mechanism-breakdown.png`](june/first-tries/2026-06-14-mechanism-breakdown.png) | The echo split into its mechanisms. |
| [`2026-06-14-absorber-physics.png`](june/first-tries/2026-06-14-absorber-physics.png) | The Salisbury screen and the Dallenbach layer: how much each absorbs against frequency, how each is built, and what it does to the stealth aircraft. |
| [`2026-06-14-edge-map.png`](june/first-tries/2026-06-14-edge-map.png) | Where the diffracting edges are on each aircraft. |
| [`2026-06-19-double-bounce-map.png`](june/first-tries/2026-06-19-double-bounce-map.png) | Which facet pairs the program counted as corner reflectors, summed over 15° to 75°, 19 June. Many of these pairs cannot actually exchange a ray (see the errata). |

## July

Shanthosh's extension, 16 and 17 July 2026: all 21 of its figures.

| | |
|---|---|
| [`bistatic.png`](july/bistatic.png) | RCS against bistatic angle, transmitter at broadside. |
| [`bistatic-nose-transmitter.png`](july/bistatic-nose-transmitter.png) | Transmitter nose-on, receiver all the way round. |
| [`polarimetric.png`](july/polarimetric.png) | The echo in each polarization, HH, VV, HV and VH, round the circle. |
| [`polarimetric-signatures.png`](july/polarimetric-signatures.png) | The four polarizations at three angles. |
| [`sibc-materials.png`](july/sibc-materials.png) | Real skin materials (aluminium 2024, stainless 304, titanium 6Al-4V, carbon-fibre composite) against a perfect conductor. |
| [`sibc-frequency.png`](july/sibc-frequency.png) | How much less each material reflects than a perfect conductor, against frequency. |
| [`sibc-reduction.png`](july/sibc-reduction.png) | The average drop for each material: at most a tenth of a dB. |
| [`optimizer.png`](july/optimizer.png) | The stealth aircraft's echo before and after the differential-evolution optimizer. |
| [`optimizer-progress.png`](july/optimizer-progress.png) | The optimizer's best mean RCS, generation by generation. |
| [`wideband-frequency.png`](july/wideband-frequency.png) | Nose-on RCS across a wide band, for the range profiles. |
| [`range-profile.png`](july/range-profile.png) | Range profiles, nose-on: the echo against distance along the line of sight. |
| [`isar.png`](july/isar.png) | ISAR images from 8 to 12 GHz over ±5° around broadside. |
| [`mesh-convergence.png`](july/mesh-convergence.png) | The basic convergence study, up to 76 million facets. |
| [`convergence-bistatic.png`](july/convergence-bistatic.png), [`convergence-polarimetric.png`](july/convergence-polarimetric.png), [`convergence-triple-bounce.png`](july/convergence-triple-bounce.png), [`convergence-triple-bounce-polarimetric.png`](july/convergence-triple-bounce-polarimetric.png), [`convergence-sibc.png`](july/convergence-sibc.png), [`convergence-optimizer.png`](july/convergence-optimizer.png), [`convergence-wideband.png`](july/convergence-wideband.png), [`convergence-isar.png`](july/convergence-isar.png) | The convergence study for each extension. |
