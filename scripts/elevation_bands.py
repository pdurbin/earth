"""Build filled land elevation bands from the thinned ETOPO 2022 grid.

Each feature covers everywhere at least `elevation` meters high, so drawing them from
low to high colors each spot by its band, and each band's outline is that contour line.
Run scripts/fetch_etopo.py first.

    python3 scripts/elevation_bands.py [input.npy] [output.geojson]
    # defaults: build/etopo_5min.npy -> data/etopo_2022_elevation_bands.geojson
"""
import json
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import LinearRing, Polygon, mapping
from shapely.ops import polygonize, unary_union
from skimage.filters import gaussian
from skimage.measure import find_contours

LEVELS = [200, 500, 1000, 1500, 2000, 3000, 4000, 5000]  # meters; keep in sync with ELEVATION_COLOR
CELL = 5 / 60     # degrees per grid cell
TOL = 0.04        # simplification, degrees (~4 km)
MIN_AREA = 0.05   # drop pieces and holes smaller than this, square degrees


def round_coords(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 3), round(c[1], 3)]
    return [round_coords(x) for x in c]


def main():
    root = Path(__file__).resolve().parent.parent
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'build' / 'etopo_5min.npy'
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else root / 'data' / 'etopo_2022_elevation_bands.geojson'

    z = gaussian(np.load(src), sigma=1, preserve_range=True)  # soften 9 km pixel noise so edges aren't jagged
    z = np.pad(z, 1, constant_values=-1e4)                     # so every contour closes into a ring
    rows, cols = z.shape

    def to_lnglat(rc):
        r, c = rc[:, 0] - 1, rc[:, 1] - 1  # undo the padding
        return np.column_stack([np.clip(-180 + (c + 0.5) * CELL, -180, 180),
                                np.clip(90 - (r + 0.5) * CELL, -90, 90)])

    def value_at(x, y):
        c = int((x + 180) / CELL - 0.5) + 1
        r = int((90 - y) / CELL - 0.5) + 1
        return z[min(max(r, 0), rows - 1), min(max(c, 0), cols - 1)]

    features = []
    for level in LEVELS:
        rings = [LinearRing(to_lnglat(rc)) for rc in find_contours(z, level) if len(rc) >= 4]
        faces = polygonize(unary_union(rings))  # split the plane along every contour ring
        band = unary_union([f for f in faces if value_at(*f.representative_point().coords[0]) >= level])
        polys = band.geoms if band.geom_type == 'MultiPolygon' else [band]
        kept = 0
        for p in polys:
            p = Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area >= MIN_AREA])
            p = p.simplify(TOL, preserve_topology=True)
            if p.area < MIN_AREA:
                continue
            g = mapping(p)
            features.append({'type': 'Feature', 'properties': {'elevation': level},
                             'geometry': {'type': g['type'], 'coordinates': round_coords(g['coordinates'])}})
            kept += 1
        print(f'{level} m: {kept} polygons', flush=True)

    with open(dst, 'w') as fh:
        json.dump({'type': 'FeatureCollection', 'features': features}, fh, separators=(',', ':'))
    print(f'saved {dst}: {dst.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
