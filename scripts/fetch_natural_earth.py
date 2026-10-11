"""Download the Natural Earth layers the map uses and trim them to what it needs.

Keeps only the properties index.html reads, rounds coordinates, and drops repeated
points, which makes the files several times smaller. Uses only the standard library.

    python3 scripts/fetch_natural_earth.py [output_dir]   # default: data/
"""
import json
import sys
import urllib.request
from pathlib import Path

BASE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/'

# file name: (properties to keep, decimal places for coordinates)
LAYERS = {
    'ne_50m_admin_0_countries': (['NAME', 'CONTINENT', 'MAPCOLOR7'], 3),
    'ne_50m_lakes': (['name'], 3),
    'ne_50m_rivers_lake_centerlines': (['name', 'scalerank'], 3),
    'ne_10m_populated_places_simple': (['name', 'scalerank'], 4),
}


def round_coords(c, places):
    if not c:
        return c
    if isinstance(c[0], (int, float)):
        return [round(c[0], places), round(c[1], places)]
    out = [round_coords(x, places) for x in c]
    if out and out[0] and isinstance(out[0][0], (int, float)):  # a line or ring: drop repeated points
        out = [out[0]] + [p for i, p in enumerate(out[1:], 1) if p != out[i - 1]]
    return out


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'data'
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, (keep, places) in LAYERS.items():
        print(f'{name}: downloading', flush=True)
        with urllib.request.urlopen(BASE + name + '.geojson') as r:
            d = json.load(r)
        features = [{
            'type': 'Feature',
            'properties': {k: f['properties'].get(k) for k in keep},
            'geometry': {'type': f['geometry']['type'],
                         'coordinates': round_coords(f['geometry']['coordinates'], places)},
        } for f in d['features']]  # drops each feature's bbox, which the map doesn't use
        out = {'type': 'FeatureCollection', 'features': features}
        path = out_dir / f'{name}.geojson'
        with open(path, 'w') as fh:
            json.dump(out, fh, separators=(',', ':'), ensure_ascii=False)
        print(f'{name}: {len(features)} features, {path.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
