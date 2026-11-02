"""Reference-atlas imagery from IRSA (no CDS dependency).

All-sky HiPS tile servers (CDS alasky) are unreachable on some networks, so
the reference view falls back to all-sky *atlas images* served by IRSA itself:
AllWISE atlas tiles (~1.5 deg, mid-infrared) and 2MASS atlas tiles (8.5 arcmin,
near-infrared).  The backend downloads the tile, extracts a WCS-preserved
cutout around the target, and serves a compact FITS that Aladin Lite can
display directly as an aligned background layer.
"""
from __future__ import annotations

import csv
import io
import math
import time
from functools import lru_cache
from urllib.parse import urlencode

import httpx
import numpy as np

from .archive import metadata_number

SIA_URL = 'https://irsa.ipac.caltech.edu/SIA'
IBE_SIA_URL = 'https://irsa.ipac.caltech.edu/ibe/sia'
MAX_TILE_BYTES = 90_000_000
MAX_OUTPUT_PX = 900


class AtlasError(Exception):
    pass


@lru_cache(maxsize=24)
def _sia_records(collection: str, ra: float, dec: float, radius_deg: float, use_ibe: bool):
    params = {
        'POS': f'CIRCLE {ra:.8f} {dec:.8f} {radius_deg:.8f}',
        'RESPONSEFORMAT': 'CSV', 'MAXREC': '40', 'DPTYPE': 'image',
    }
    base = IBE_SIA_URL if use_ibe else SIA_URL
    if use_ibe:
        params['collection'] = collection
        params['LEVEL'] = 'atl'
    else:
        params['COLLECTION'] = collection
    last_exc = None
    for attempt in range(2):
        try:
            with httpx.Client(timeout=httpx.Timeout(60.0, connect=15.0), follow_redirects=False) as client:
                response = client.get(base, params=params)
                response.raise_for_status()
                payload = response.text
            header = next(csv.reader(io.StringIO(payload.lstrip('\ufeff'))), [])
            if 'access_url' not in header:
                return []
            return [row for row in csv.DictReader(io.StringIO(payload.lstrip('\ufeff')))
                    if (row.get('access_url') or '').strip()]
        except httpx.HTTPError as exc:
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    raise AtlasError(f'IRSA SIA unreachable for {collection}: {type(last_exc).__name__}')


def _nearest_tile(rows: list[dict], ra: float, dec: float) -> dict | None:
    best, best_sep = None, None
    for row in rows:
        s_ra, s_dec = metadata_number(row, 's_ra'), metadata_number(row, 's_dec')
        if s_ra is None or s_dec is None:
            continue
        d_ra = (s_ra - ra) * math.cos(math.radians(dec))
        sep = math.hypot(d_ra, s_dec - dec)
        if best_sep is None or sep < best_sep:
            best, best_sep = row, sep
    return best


def _download(url: str) -> bytes:
    last_exc = None
    for attempt in range(3):
        try:
            with httpx.Client(timeout=httpx.Timeout(180.0, connect=15.0), follow_redirects=False) as client:
                with client.stream('GET', url) as response:
                    response.raise_for_status()
                    total = 0
                    parts = []
                    for chunk in response.iter_bytes():
                        total += len(chunk)
                        if total > MAX_TILE_BYTES:
                            raise AtlasError('Reference tile exceeds the size limit.')
                        parts.append(chunk)
                    return b''.join(parts)
        except httpx.HTTPError as exc:
            last_exc = exc
            time.sleep(2.0 * (attempt + 1))
    raise AtlasError(f'Reference tile download failed: {type(last_exc).__name__}') from last_exc


@lru_cache(maxsize=16)
def atlas_fits(ra: float, dec: float, fov_arcmin: float, survey: str = 'wise') -> bytes:
    """Return a compact WCS-preserved FITS cutout of reference imagery."""
    surveys = {
        # AllWISE Atlas coadds: ~1.56 deg tiles, W1-W4 mid-infrared.
        'wise': {'collection': 'allwise', 'use_ibe': True, 'max_fov': 60.0},
        # 2MASS Atlas tiles: ~8.5 arcmin, J/H/K near-infrared.
        '2mass': {'collection': '2mass', 'use_ibe': True, 'max_fov': 7.0},
    }
    if survey not in surveys:
        raise AtlasError(f'Unknown reference survey {survey!r}.')
    spec = surveys[survey]
    if fov_arcmin > spec['max_fov']:
        raise AtlasError(f'{survey.upper()} reference tiles support fields up to '
                         f"{spec['max_fov']:.0f}' ; narrow the field of view.")
    radius_deg = max(0.05, (fov_arcmin / 60.0) * 0.75)
    rows = _sia_records(spec['collection'], round(ra, 6), round(dec, 6),
                        round(radius_deg, 6), spec['use_ibe'])
    if not rows and spec['use_ibe'] is True:
        rows = _sia_records(spec['collection'], round(ra, 6), round(dec, 6),
                            round(radius_deg, 6), False)
    if not rows:
        raise AtlasError(f'No {survey.upper()} atlas imagery covers this field in IRSA.')
    tile = _nearest_tile(rows, ra, dec)
    if not tile:
        raise AtlasError('No usable reference tile record returned.')
    tile_url = (tile.get('access_url') or '').strip()
    if not tile_url.lower().endswith(('.fits', '.fits.gz')):
        raise AtlasError('The returned reference record is not a FITS image.')
    tile_bytes = _download(tile_url)
    return _make_cutout(tile_bytes, ra, dec, fov_arcmin, survey)


def _make_cutout(tile_bytes: bytes, ra: float, dec: float, fov_arcmin: float,
                 survey: str) -> bytes:
    from astropy.io import fits
    from astropy.nddata import Cutout2D
    from astropy.wcs import WCS
    try:
        with fits.open(io.BytesIO(tile_bytes), memmap=False, lazy_load_hdus=False) as hdul:
            sci = hdul[0] if hdul[0].data is not None else hdul[1]
            data = np.asarray(sci.data, dtype=np.float32)
            wcs = WCS(sci.header, hdul).celestial if hdul[0].data is None else WCS(sci.header).celestial
            bunit = str(sci.header.get('BUNIT', '')).strip()
    except (OSError, ValueError) as exc:
        raise AtlasError(f'Cannot read reference tile: {type(exc).__name__}') from exc
    if data.ndim != 2:
        raise AtlasError('Reference tile is not a 2-D image.')
    try:
        cut = Cutout2D(data, (ra, dec), (fov_arcmin / 60.0, fov_arcmin / 60.0), wcs=wcs)
    except (ValueError, IndexError) as exc:
        raise AtlasError('Target position falls outside the reference tile.') from exc
    step = max(1, int(math.ceil(max(cut.data.shape) / MAX_OUTPUT_PX)))
    small = cut.data[::step, ::step]
    small_wcs = cut.wcs[::step, ::step]
    valid = np.isfinite(small)
    if valid.any():
        lo, hi = np.percentile(small[valid], [1, 99.4])
        if not np.isfinite(hi - lo) or hi <= lo:
            hi = lo + 1
        scaled = np.clip((small - lo) / (hi - lo), 0, 1)
        out = (np.arcsinh(9 * scaled) / math.asinh(9) * 255).astype(np.uint8)
    else:
        out = np.zeros_like(small, dtype=np.uint8)
    header = small_wcs.to_header()
    header['BUNIT'] = 'display-stretch (0-255 asinh)'
    header['ORIGBUNIT'] = bunit or 'unknown'
    header['ORIGIN'] = f'IRSA {survey.upper()} atlas via SPHEREx Motion Explorer'
    buffer = io.BytesIO()
    fits.PrimaryHDU(out, header=header).writeto(buffer, overwrite=True)
    return buffer.getvalue()
