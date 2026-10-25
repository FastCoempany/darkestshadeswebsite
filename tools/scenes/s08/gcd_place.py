"""The GCD (gcd_render's model, from the vector master) on an end piece's triangle platform."""
import os
import re
import sys

import numpy as np
from mathutils import Matrix

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "blender"))
import frame3d  # noqa: E402,F401
import gcd_render  # noqa: E402

MM = 0.001


def add_gcd(end, length_mm=8.8, proud_mm=0.12):
    """The emblem centred on the triangle platform (end["centre"], its area centroid, on the outer face),
    lying on that face, its long axis along the temple. Seen from outside it reads as the master does
    (the big lobe toward the temple), so its x runs toward the front on the wearer's right piece."""
    svg = gcd_render.GEOM.read_text()
    outer = re.search(r'id="outer"\s+d="([^"]+)"', svg).group(1)
    aperture = re.search(r'id="aperture"\s+d="([^"]+)"', svg).group(1)
    osp, asp = gcd_render.parse_path(outer), gcd_render.parse_path(aperture)
    gold = gcd_render.curve_object("gcd gold", osp + asp, gcd_render.GOLD_DEPTH, gcd_render.GOLD_BEVEL, 0.0)
    stone = gcd_render.curve_object("gcd onyx", asp, gcd_render.GOLD_DEPTH - 2 * gcd_render.STONE_RECESS,
                                    gcd_render.STONE_BEVEL, -gcd_render.STONE_RECESS)
    gold.data.materials.append(gcd_render.gold_material())
    stone.data.materials.append(gcd_render.onyx_material(None))
    gold, stone = frame3d.to_mesh(gold), frame3d.to_mesh(stone)
    nrm = np.asarray(end["normal"], np.float64)
    nrm /= np.linalg.norm(nrm)
    up = np.array([0.0, 1.0, 0.0]) - nrm * nrm[1]
    up /= np.linalg.norm(up)
    ex = np.cross(up, nrm)                      # seen from outside: the viewer's right
    Rm = np.stack([ex, up, nrm], 1)             # a proper rotation (ex x up = nrm)
    s = length_mm / (gcd_render.LENGTH_M / MM)
    M = Matrix.Identity(4)
    for i in range(3):
        for j in range(3):
            M[i][j] = Rm[i, j] * s
    pos = (np.asarray(end["centre"], np.float64) + nrm * proud_mm) * MM
    M[0][3], M[1][3], M[2][3] = pos
    for ob in (gold, stone):
        ob.matrix_world = M
    return [gold, stone]
