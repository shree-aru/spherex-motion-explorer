"""Reference-atlas imagery from IRSA AllWISE coadds (no CDS dependency).

All-sky HiPS tile servers (CDS alasky) are unreachable on some networks, so
the reference view uses the AllWISE coadded atlas images served by IRSA's
Image Backend (IBE): ~1.5 deg W1-W4 coadds covering the entire sky.  The
backend locates the coadd tile containing the target via the IBE search API,
downloads an official IBE cutout, and serves a compact WCS-preserved FITS
that Aladin Lite displays directly as an aligned background layer.
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

IBE_BASE = 'https://irsa.ipac.caltech.edu/ibe'
MAX_TILE_BYTES = 60_000_000
MAX_OUTPUT_PX = 900
BAND = '1'  # W1 (3.4 um): deepest AllWISE band, stellar continuum


class AtlasError(Exception):
    pass


@lru_cache(maxsize=32)
def _ibe_search(ra: float, dec: float):
    """Locate the AllWISE coadd tile(s) containing a position."""
    params = {'POS': f'{ra:.6f},{dec:.6f}', 'RESPONSEFORMAT': 'csv'}
    url = f'{IBE_BASE}/search/wise/allwise/p3am_cdd'
    last_exc = None
    for attempt in range(3):
        try:
            with httpx.Client(timeout=httpx.Timeout(60.0, connect=15.0), follow_redirects=False) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                payload = response.text
            if '<VOTABLE' in payload[:200]:
                marker = 'value="ERROR"'
                if marker in payload:
                    start = payload.find(marker)
                    excerpt = payload[start:payload.find('</INFO>', start)]
                    raise AtlasError(f'IRSA IBE rejected the reference query: {excerpt[:160]}')
                return []
            rows = [row for row in csv.DictReader(io.StringIO(payload.lstrip('\ufeff')))
                    if row.get('coadd_id') and row.get('band') == BAND]
            return rows
        except httpx.HTTPError as exc:
            last_exc = exc
            time.sleep(2.0 * (attempt + 1))
    raise AtlasError(f'IRSA IBE unreachable: {type(last_exc).__name__}') from last_exc


def _pick_tile(rows: list[dict], ra: float, dec: float) -> dict:
    """Nearest coadd centre wins (tiles overlap at the edges)."""
    best, best_sep = None, None
    for row in rows:
        try:
            c_ra, c_dec = float(row['crval1']), float(row['crval2'])
        except (KeyError, ValueError, TypeError):
            continue
        d_ra = (c_ra - ra) * math.cos(math.radians(dec))
        sep = math.hypot(d_ra, c_dec - dec)
        if best_sep is None or sep < best_sep:
            best, best_sep = row, sep
    if not best:
        raise AtlasError('No usable AllWISE coadd tile in the IRSA response.')
    return best


def _download_cutout(url: str) -> bytes:
    last_exc = None
    for attempt in range(3):
        try:
            with httpx.Client(timeout=httpx.Timeout(180.0, connect=15.0), follow_redirects=False) as client:
                with client.stream('GET', url) as response:
                    response.raise_for_status()
                    total, parts = 0, []
                    for chunk in response.iter_bytes():
                        total += len(chunk)
                        if total > MAX_TILE_BYTES:
                            raise AtlasError('Reference cutout exceeds the size limit.')
                        parts.append(chunk)
                    return b''.join(parts)
        except httpx.HTTPError as exc:
            last_exc = exc
            time.sleep(2.0 * (attempt + 1))
    raise AtlasError(f'Reference cutout download failed: {type(last_exc).__name__}') from last_exc


@lru_cache(maxsize=16)
def atlas_fits(ra: float, dec: float, fov_arcmin: float, survey: str = 'wise') -> bytes:
    """Compact WCS-preserved display FITS of AllWISE imagery around a target."""
    if fov_arcmin > 60.0:
        raise AtlasError('Reference imagery supports fields up to 60 arcmin; narrow the field of view.')
    rows = _ibe_search(round(ra, 6), round(dec, 6))
    if not rows:
        raise AtlasError('No AllWISE coadd tile covers this position in IRSA.')
    tile = _pick_tile(rows, ra, dec)
    coadd_id = tile['coadd_id'].strip()
    # Docs example: 03/0390/0390p605_ac51/0390p605_ac51-w1-int-3.fits
    tile_url = (f'{IBE_BASE}/data/wise/allwise/p3am_cdd/'
                f"{coadd_id[:2]}/{coadd_id[:4]}/{coadd_id}/{coadd_id}-w{BAND}-int-3.fits")
    size_deg = min(max(fov_arcmin / 60.0 * 1.2, 0.05), 1.3)
    cutout_url = tile_url + '?' + urlencode({'center': f'{ra:.6f},{dec:.6f}', 'size': f'{size_deg:.6f}'})
    tile_bytes = _download_cutout(cutout_url)
    if tile_bytes[:2] == b'\x1f\x8b':  # IBE serves gzip-compressed FITS cutouts
        import gzip
        tile_bytes = gzip.decompress(tile_bytes)
    return _make_display_fits(tile_bytes, ra, dec, fov_arcmin)


def _make_display_fits(tile_bytes: bytes, ra: float, dec: float, fov_arcmin: float) -> bytes:
    from astropy.io import fits
    from astropy.wcs import WCS
    try:
        with fits.open(io.BytesIO(tile_bytes), memmap=False, lazy_load_hdus=False) as hdul:
            sci = hdul[0] if hdul[0].data is not None else hdul[1]
            data = np.asarray(sci.data, dtype=np.float32)
            header_in = sci.header
    except (OSError, ValueError) as exc:
        raise AtlasError(f'Cannot read the reference cutout: {type(exc).__name__}') from exc
    if data.ndim != 2:
        raise AtlasError('Reference cutout is not a 2-D image.')
    valid = np.isfinite(data)
    if not valid.any():
        raise AtlasError('The reference cutout contains no usable pixels.')
    lo, hi = np.percentile(data[valid], [1, 99.4])
    if not np.isfinite(hi - lo) or hi <= lo:
        hi = lo + 1
    scaled = np.clip((data - lo) / (hi - lo), 0, 1)
    out = (np.arcsinh(9 * scaled) / math.asinh(9) * 255).astype(np.uint8)
    try:
        wcs = WCS(header_in).celestial
        header = wcs.to_header()
    except Exception:
        header = fits.Header()
    header['BUNIT'] = 'display-stretch (0-255 asinh)'
    header['ORIGIN'] = 'IRSA AllWISE coadd via SPHEREx Motion Explorer'
    header['WAVELEN'] = (3.4, 'W1 effective wavelength [um]')
    buffer = io.BytesIO()
    fits.PrimaryHDU(out, header=header).writeto(buffer, overwrite=True)
    return buffer.getvalue()
