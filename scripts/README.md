# Data scripts

These scripts rebuild everything in `data/`. You only need them to refresh or change the
data; the map itself just loads the files in `data/`.

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt

# Natural Earth countries, lakes, rivers and cities, trimmed (standard library only)
.venv/bin/python scripts/fetch_natural_earth.py

# NOAA ETOPO 2022 elevation, every 5th point (~37 MB download, saved to build/)
.venv/bin/python scripts/fetch_etopo.py

# Land elevation bands from that grid
.venv/bin/python scripts/elevation_bands.py
```

| Script | Output | Source |
|---|---|---|
| `fetch_natural_earth.py` | `data/ne_*.geojson` | [Natural Earth](https://www.naturalearthdata.com/) (public domain) |
| `fetch_etopo.py` | `build/etopo_5min.npy` (not committed) | [NOAA ETOPO 2022](https://www.ncei.noaa.gov/products/etopo-global-relief-model) (public domain) |
| `elevation_bands.py` | `data/etopo_2022_elevation_bands.geojson` | the ETOPO grid above |

To change the elevation bands, edit `LEVELS` in `elevation_bands.py` and the matching
`ELEVATION_COLOR` steps in `index.html`.
