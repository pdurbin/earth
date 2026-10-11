"""Download NOAA ETOPO 2022 elevation, thinned to every 5th point (5 arc-minutes, ~9 km).

The full 1 arc-minute file is 478 MB; NOAA's OPeNDAP server can send every 5th row and
column instead (about 37 MB), which is plenty for this map. The result is saved as a
north-up NumPy array (2160 x 4320, meters) starting at 180°W, 90°N.

    python3 scripts/fetch_etopo.py [output.npy]   # default: build/etopo_5min.npy
"""
import sys
import urllib.request
from pathlib import Path

import numpy as np

URL = ('https://www.ngdc.noaa.gov/thredds/dodsC/global/ETOPO2022/60s/60s_surface_elev_netcdf/'
       'ETOPO_2022_v1_60s_N90W180_surface.nc.dods?z.z[2:5:10799][2:5:21599]')
ROWS, COLS = 2160, 4320


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'build' / 'etopo_5min.npy'
    out.parent.mkdir(parents=True, exist_ok=True)
    print('downloading ETOPO 2022 (about 37 MB)...', flush=True)
    with urllib.request.urlopen(URL) as r:
        raw = r.read()
    # A DAP2 binary response: a text header, "Data:", then the array as two big-endian
    # uint32 lengths followed by big-endian float32 values. Rows run south to north.
    start = raw.index(b'\nData:\n') + len(b'\nData:\n')
    n = int(np.frombuffer(raw[start:start + 4], '>u4')[0])
    assert n == ROWS * COLS, f'unexpected size {n}'
    z = np.frombuffer(raw[start + 8:start + 8 + 4 * n], '>f4').reshape(ROWS, COLS)
    np.save(out, z[::-1].astype(np.float32))  # flip to north-up
    print(f'saved {out}: elevation {z.min():.0f} to {z.max():.0f} m')


if __name__ == '__main__':
    main()
