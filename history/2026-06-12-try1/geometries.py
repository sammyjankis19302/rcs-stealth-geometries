"""
geometries.py
=============
Triangulated mesh definitions for:
  - Sphere
  - Flat Plate
  - Conventional Aircraft (box fuselage, flat wings, vertical stabilizer)
  - Stealth Aircraft (F-117/B-2 inspired: faceted, swept, canted)

All coordinates in metres. Aircraft nose points in -X direction.
Radar azimuth 0° = nose-on, 90° = right broadside.
"""

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# PRIMITIVE BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _quad(p0, p1, p2, p3):
    """Return (vertices[4,3], faces[2,3]) for a planar quad."""
    v = np.array([p0, p1, p2, p3], dtype=float)
    f = np.array([[0, 1, 2], [0, 2, 3]])
    return v, f


def _box(xmin, xmax, ymin, ymax, zmin, zmax):
    """Return (vertices[8,3], faces[12,3]) for a closed box."""
    v = np.array([
        [xmin, ymin, zmin], [xmax, ymin, zmin],
        [xmax, ymax, zmin], [xmin, ymax, zmin],
        [xmin, ymin, zmax], [xmax, ymin, zmax],
        [xmax, ymax, zmax], [xmin, ymax, zmax],
    ], dtype=float)
    f = np.array([
        [0, 2, 1], [0, 3, 2],   # -Z face
        [4, 5, 6], [4, 6, 7],   # +Z face
        [0, 1, 5], [0, 5, 4],   # -Y face
        [3, 7, 6], [3, 6, 2],   # +Y face
        [1, 2, 6], [1, 6, 5],   # +X face
        [0, 4, 7], [0, 7, 3],   # -X face
    ])
    return v, f


def _tri(p0, p1, p2):
    v = np.array([p0, p1, p2], dtype=float)
    f = np.array([[0, 1, 2]])
    return v, f


def _combine(mesh_list):
    """Merge a list of (vertices, faces) into one mesh."""
    all_v, all_f, offset = [], [], 0
    for v, f in mesh_list:
        all_v.append(np.asarray(v, dtype=float))
        all_f.append(np.asarray(f) + offset)
        offset += len(v)
    return np.vstack(all_v), np.vstack(all_f)


# ─────────────────────────────────────────────────────────────────────────────
# GEOMETRY: SPHERE
# ─────────────────────────────────────────────────────────────────────────────

def sphere_mesh(radius=1.0, n_lat=24, n_lon=48):
    """UV-sphere triangulation."""
    verts = []
    for i in range(n_lat + 1):
        phi = -np.pi / 2 + np.pi * i / n_lat
        for j in range(n_lon):
            theta = 2 * np.pi * j / n_lon
            verts.append([
                radius * np.cos(phi) * np.cos(theta),
                radius * np.cos(phi) * np.sin(theta),
                radius * np.sin(phi),
            ])
    verts = np.array(verts)
    faces = []
    for i in range(n_lat):
        for j in range(n_lon):
            a = i * n_lon + j
            b = i * n_lon + (j + 1) % n_lon
            c = (i + 1) * n_lon + (j + 1) % n_lon
            d = (i + 1) * n_lon + j
            faces += [[a, b, c], [a, c, d]]
    return verts, np.array(faces)


# ─────────────────────────────────────────────────────────────────────────────
# GEOMETRY: FLAT PLATE
# ─────────────────────────────────────────────────────────────────────────────

def flat_plate(length=2.0, width=2.0):
    """Square flat plate in the XY plane (normal = +Z)."""
    l, w = length / 2, width / 2
    return _quad([-l, -w, 0], [l, -w, 0], [l, w, 0], [-l, w, 0])


# ─────────────────────────────────────────────────────────────────────────────
# GEOMETRY: CONVENTIONAL AIRCRAFT
# ─────────────────────────────────────────────────────────────────────────────
#
#  Design intent: LOTS of flat surfaces at 0°/90° angles.
#  Strong RCS contributors:
#    • Box fuselage sides  → broadside (90°)
#    • Flat wings          → top/bottom look angles
#    • Vertical stabilizer → broadside (90°) + corner dihedral with fuselage
#    • Flat nose face      → nose-on (0°)
#    • 90° wing-fuselage dihedral → corner reflector effect
#

def conventional_aircraft():
    meshes = []

    # ── Fuselage: simple box, flat sides give strong broadside return ──
    meshes.append(_box(-3.6, 3.6, -0.50, 0.50, -0.50, 0.50))

    # ── Main wings: flat plates, NO dihedral (0°) ──
    meshes.append(_quad(  # right wing
        [-1.2,  0.50, 0.0], [ 1.4,  0.50, 0.0],
        [ 1.4,  3.00, 0.0], [-1.2,  3.00, 0.0]))
    meshes.append(_quad(  # left wing
        [-1.2, -0.50, 0.0], [-1.2, -3.00, 0.0],
        [ 1.4, -3.00, 0.0], [ 1.4, -0.50, 0.0]))

    # ── Vertical stabilizer: perfectly vertical flat slab ──
    #    Creates a strong dihedral corner with horizontal fuselage top → classic RCS spike
    meshes.append(_box(1.6, 3.4, -0.12, 0.12, 0.50, 1.70))

    # ── Horizontal stabilizer ──
    meshes.append(_quad(  # right
        [1.6,  0.50, -0.20], [3.4,  0.50, -0.20],
        [3.4,  1.40, -0.20], [1.6,  1.40, -0.20]))
    meshes.append(_quad(  # left
        [1.6, -0.50, -0.20], [1.6, -1.40, -0.20],
        [3.4, -1.40, -0.20], [3.4, -0.50, -0.20]))

    # ── Nose face (simulates flat engine intake) ──
    meshes.append(_quad(
        [-3.6, -0.50, -0.50], [-3.6,  0.50, -0.50],
        [-3.6,  0.50,  0.50], [-3.6, -0.50,  0.50]))

    return _combine(meshes)


# ─────────────────────────────────────────────────────────────────────────────
# GEOMETRY: STEALTH AIRCRAFT
# ─────────────────────────────────────────────────────────────────────────────
#
#  Design intent: REDIRECT energy away from the threat axis (0° ± ~30°).
#  Key principles applied:
#    • All vertical surfaces canted (no 90° walls facing the radar)
#    • Fuselage has trapezoidal cross-section (angled sides)
#    • Delta wings with ~65° leading-edge sweep → leading edge spike off nose axis
#    • V-tail canted 35° outward, no perpendicular fin surface
#    • Pointed nose → tiny nose-on area
#    • No right-angle dihedrals → no corner-reflector effect
#

def stealth_aircraft():
    meshes = []
    c = np.radians(35)   # cant angle for V-tail

    # ── Fuselage: trapezoidal cross-section (wide bottom, narrower top) ──
    #   Top panel (flat, but tilted slightly)
    meshes.append(_quad(
        [-3.2, -0.38, 0.46], [-3.2,  0.38, 0.46],
        [ 3.0,  0.38, 0.46], [ 3.0, -0.38, 0.46]))
    #   Bottom panel
    meshes.append(_quad(
        [-3.2, -0.55, -0.12], [ 3.0, -0.55, -0.12],
        [ 3.0,  0.55, -0.12], [-3.2,  0.55, -0.12]))
    #   Right side (angled inward ~20°)
    meshes.append(_quad(
        [-3.2,  0.38, 0.46], [ 3.0,  0.38, 0.46],
        [ 3.0,  0.55, -0.12], [-3.2,  0.55, -0.12]))
    #   Left side (angled inward ~20°)
    meshes.append(_quad(
        [-3.2, -0.55, -0.12], [ 3.0, -0.55, -0.12],
        [ 3.0, -0.38,  0.46], [-3.2, -0.38,  0.46]))

    # ── Nose section: pointed, 4-facet pyramid → tiny frontal area ──
    tip = np.array([-5.2, 0.0, 0.17])
    base = [
        np.array([-3.2, -0.38, -0.12]),
        np.array([-3.2,  0.38, -0.12]),
        np.array([-3.2,  0.38,  0.46]),
        np.array([-3.2, -0.38,  0.46]),
    ]
    for i in range(4):
        meshes.append(_tri(base[i], base[(i+1) % 4], tip))

    # ── Highly swept delta wings (~65° LE sweep) ──
    #    Leading edge spike occurs at ~65° from nose-on → non-threatening sector
    meshes.append(_quad(  # right wing
        [-0.4,  0.55, -0.10], [ 2.6,  0.55, -0.10],
        [-1.8,  3.40, -0.10], [-3.2,  3.40, -0.10]))
    meshes.append(_quad(  # left wing
        [-0.4, -0.55, -0.10], [-3.2, -3.40, -0.10],
        [-1.8, -3.40, -0.10], [ 2.6, -0.55, -0.10]))

    # ── Canted V-tails: angled 35° outward, no vertical wall ──
    meshes.append(_quad(  # right V-tail
        [ 2.0,  0.38,  0.46],
        [ 3.2,  0.38,  0.46],
        [ 3.2,  0.38 + 0.95*np.sin(c),  0.46 + 0.95*np.cos(c)],
        [ 2.0,  0.38 + 0.65*np.sin(c),  0.46 + 0.65*np.cos(c)]))
    meshes.append(_quad(  # left V-tail
        [ 2.0, -0.38,  0.46],
        [ 2.0, -0.38 - 0.65*np.sin(c),  0.46 + 0.65*np.cos(c)],
        [ 3.2, -0.38 - 0.95*np.sin(c),  0.46 + 0.95*np.cos(c)],
        [ 3.2, -0.38,  0.46]))

    return _combine(meshes)


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

GEOMETRIES = {
    "Sphere (r=1m)":             lambda: sphere_mesh(radius=1.0),
    "Flat Plate (2×2 m)":        lambda: flat_plate(2.0, 2.0),
    "Conventional Aircraft":     conventional_aircraft,
    "Stealth Aircraft":          stealth_aircraft,
}
