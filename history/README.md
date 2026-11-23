# How the code grew

Each folder is the code exactly as it was on that day, mistakes included. The corrected version is in
[`../rcs`](../rcs).

| Folder | Date | What it added |
|---|---|---|
| [`2026-06-12-try1`](2026-06-12-try1) | 12 June 2026 | Physical Optics on the sphere, flat plate, conventional and stealth aircraft; the Mie series for the sphere |
| [`2026-06-14-try2`](2026-06-14-try2) | 14 June | Bistatic sweeps; the flying wing and the chined-nose aircraft |
| [`2026-06-14-try3`](2026-06-14-try3) | 14 June | PO rebuilt as the base for higher-order terms; edge diffraction (PTD fringe term), double bounce, Salisbury screen and Dallenbach absorbers, the mechanism breakdown |
| [`2026-06-20-june-final`](2026-06-20-june-final) | 20 June | The program behind the June draft report and its 64 figures (tries 4 to 8 polished this; the physics is the same from try 4 on) |
| [`2026-07-17-july-extension`](2026-07-17-july-extension) | 16–17 July | Shanthosh's extension with another AI agent: bistatic and polarimetric scattering, triple bounce, surface-impedance materials, the shape optimizer, wideband range profiles, ISAR, and the convergence studies; behind the final report, slides and poster |

To run one, go into its folder and run its main script (`main.py`, `main2.py` or `main3.py`); the
July studies run the same way. The June and July versions write their figures to `output_ppt/`.

What the November 2026 checks changed is listed in the main [README](../README.md#what-we-checked-in-november-2026).
