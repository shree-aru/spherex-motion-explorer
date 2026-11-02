"""Exploratory on-the-fly spectrophotometry from official IRSA SPHEREx cutouts.

Each SPHEREx L2b file covers one detector band at one epoch; the linear
variable filter means the local wavelength at a sky position depends on where
it lands on the detector.  Collecting many files and pairing each aperture
flux with its *local* wavelength (WCS-WAVE lookup) builds a low-resolution
spectrum.  This is a visualization/education product: statistical errors only,
no calibrated spectrophotometry.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Sequence

import numpy as np

from .flags import fatal_mask
from .science import ScienceError, local_wavelength, open_cutout

APERTURE_RADIUS_PX = 2.0
ANNULUS_INNER_PX = 3.0
ANNULUS_OUTER_PX = 6.0
DETECTOR_RE = re.compile(r'D([1-6])(?=_spx)')


def _detector_from_source(source: str) -> str:
    match = DETECTOR_RE.search(source)
    return f'D{match.group(1)}' if match else 'Unknown'


def extract_point(source: str, ra: float, dec: float, fov: float) -> dict:
    """Aperture flux + local wavelength for one archive file at one position.

    Bright targets saturate SPHEREx cores, and the saturation-family flags
    (OVERFLOW/BLOOM/HALO) then mask the whole photometric aperture.  In that
    case the extractor retries with the display-level mask and marks the
    point, so bright-source spectra remain usable and honestly labelled.
    """
    products = open_cutout(source, ra, dec, fov)
    hdul = products['hdul']
    try:
        data, src_wcs = products['data'], products['wcs']
        finite = np.isfinite(data)
        flags = products['flags'] if (products['flags'] is not None
                                      and products['flags'].shape == data.shape) else None
        if flags is not None:
            strict_valid = finite & ~fatal_mask(flags, 'strict')
        else:
            strict_valid = finite
        if not strict_valid.any() and not finite.any():
            raise ScienceError('All pixels in this cutout are flagged or non-finite.')
        x0, y0 = (float(v) for v in src_wcs.all_world2pix(ra, dec, 0))
        h, w = data.shape
        if not (-1 <= x0 <= w and -1 <= y0 <= h):
            raise ScienceError('Target position falls outside this exposure.')
        yy, xx = np.mgrid[0:h, 0:w]
        radius = np.hypot(xx - x0, yy - y0)

        def measure(valid_mask: np.ndarray) -> tuple[int, int, float, float]:
            aperture = valid_mask & (radius <= APERTURE_RADIUS_PX)
            annulus = valid_mask & (radius > ANNULUS_INNER_PX) & (radius <= ANNULUS_OUTER_PX)
            n_ap = int(aperture.sum())
            n_ann = int(annulus.sum())
            background = float(np.median(data[annulus])) if n_ann >= 4 else 0.0
            return n_ap, n_ann, background, float(np.sum(data[aperture] - background)) if n_ap else 0.0

        n_ap, n_ann, background, flux = measure(strict_valid)
        mask_level = 'strict'
        saturated = False
        if n_ap < 2 and flags is not None:
            display_valid = finite & ~fatal_mask(flags, 'display')
            n_ap_d, n_ann_d, background_d, flux_d = measure(display_valid)
            if n_ap_d > n_ap:
                n_ap, n_ann, background, flux = n_ap_d, n_ann_d, background_d, flux_d
                mask_level = 'display'
                saturated = True
        if n_ap == 0:
            raise ScienceError('No valid pixels inside the photometric aperture.')
        err = None
        if products['variance'] is not None and products['variance'].shape == data.shape:
            var = products['variance']
            ap_valid = (strict_valid if mask_level == 'strict' else finite) & (radius <= APERTURE_RADIUS_PX)
            err = float(np.sqrt(np.sum(var[ap_valid]))) + 1e-12
        wave = {'lambda_um': None, 'bandwidth_um': None}
        if products['wave_table'] is not None:
            wave = local_wavelength(products['header'], products['wave_table'], src_wcs, ra, dec)
        if wave['lambda_um'] is None:
            raise ScienceError(f"Local wavelength unavailable: {wave.get('reason')}")
        point = {
            'lambda_um': wave['lambda_um'],
            'bandwidth_um': wave['bandwidth_um'],
            'flux_MJy_sr': round(flux, 4),
            'err_stat_MJy_sr': round(err, 4) if err is not None else None,
            'snr': round(flux / err, 2) if err else None,
            'background_MJy_sr': round(background, 4),
            'aperture_pixels': n_ap,
            'mask_level': mask_level,
            'saturated_core': saturated,
            'detector': _detector_from_source(source),
            'source_url': source,
        }
        zodi = products['zodi']
        if zodi is not None and zodi.shape == data.shape:
            point['zodi_median_MJy_sr'] = round(float(np.nanmedian(zodi[finite])), 4)
        return point
    finally:
        hdul.close()


CENTERED_LIMIT_ARCMIN = 85.0  # ~25' clearance from the 110' detector half-width


def _sample_files(rows: Sequence[dict], max_files: int) -> list[dict]:
    """Evenly sample across wavelength, preferring frames where the target sits
    well inside the detector (SPHEREx frames are ~3.5 deg across, so SIA
    'intersections' often clip the field and leave the target unobservable)."""
    seen, unique = set(), []
    for row in rows:
        source = row.get('source')
        if source and source not in seen:
            seen.add(source)
            unique.append(row)
    centered = [r for r in unique
                if r.get('center_offset_arcmin') is None
                or r['center_offset_arcmin'] <= CENTERED_LIMIT_ARCMIN]
    pool = centered if len(centered) >= max_files else unique
    if len(pool) <= max_files:
        return list(pool)
    lo = [(row.get('wavelength_min_um') or 0) for row in pool]
    order = sorted(range(len(pool)), key=lambda i: lo[i])
    stride = len(order) / max_files
    return [pool[order[int(k * stride)]] for k in range(max_files)]


def extract_spectrum(ra: float, dec: float, fov: float, observations: Sequence[dict],
                     max_files: int = 40, workers: int = 6) -> dict:
    """Build a wavelength-sorted spectrum point list from many archive files."""
    files = _sample_files(observations, max_files)
    points, failed = [], []
    workers = max(1, min(workers, 8))

    def work(row: dict):
        return extract_point(row['source'], ra, dec, fov), row

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(work, row): row for row in files}
        for future in as_completed(futures):
            row = futures[future]
            try:
                point, _ = future.result()
            except ScienceError as exc:
                failed.append({'obs_id': row.get('obs_id'), 'reason': str(exc)[:120]})
                continue
            point.update({'obs_id': row.get('obs_id'), 'band': row.get('band'),
                          'date_utc': row.get('date_utc'),
                          'wavelength_file_min_um': row.get('wavelength_min_um'),
                          'wavelength_file_max_um': row.get('wavelength_max_um')})
            points.append(point)
    points.sort(key=lambda p: p['lambda_um'])
    return {'points': points, 'files_requested': len(files),
            'files_failed': failed[:12], 'files_failed_count': len(failed),
            'method': (f'Aperture sum r={APERTURE_RADIUS_PX} detector pixels, annulus background '
                       f'{ANNULUS_INNER_PX}-{ANNULUS_OUTER_PX} px, statistical errors from the '
                       'VARIANCE extension only. Saturated cores fall back to the display mask and '
                       'are flagged (saturated_core=true; flux then underestimates the source).'),
            'caveat': ('Exploratory spectrophotometry: linear-variable-filter local wavelengths are '
                       'visualization-grade (WCS-WAVE), errors are statistical only, and no aperture '
                       'correction or absolute calibration is applied. Saturated-core points '
                       '(saturated_core=true) are lower limits. Use IRSA spectrophotometry '
                       'products for science-grade spectra.')}
