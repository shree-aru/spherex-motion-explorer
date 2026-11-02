"""Registered preview imaging. No discovery claims, photometric calibration or fake sky data."""
from __future__ import annotations

import io
import math
import time
from functools import lru_cache
from urllib.parse import urlencode
from typing import Sequence

import httpx
import numpy as np
from PIL import Image

from .archive import valid_source_url
from .flags import fatal_mask, summarize_flags

MAX_CUTOUT_BYTES = 28_000_000


class ScienceError(Exception):
    pass


@lru_cache(maxsize=48)
def get_cutout_bytes(source: str, ra: float, dec: float, fov_arcmin: float) -> bytes:
    if not valid_source_url(source):
        raise ScienceError('Untrusted source URL. Only official IRSA SPHEREx FITS files are accepted.')
    # IRSA's documented service accepts `center=RA,Dec&size=degrees`.  The
    # service returns NAXIS2 ~0.42x NAXIS1 for spectral images, so pad the
    # request to guarantee full coverage of the square display field.
    size_deg = (fov_arcmin / 60) * 2.5
    url = source + '?' + urlencode({'center': f'{ra:.8f},{dec:.8f}', 'size': f'{size_deg:.7f}'})
    last_exc = None
    for attempt in range(3):  # the IRSA route can stall; retry with backoff
        try:
            with httpx.Client(timeout=httpx.Timeout(90.0, connect=20.0), follow_redirects=False) as client:
                with client.stream('GET', url) as response:
                    response.raise_for_status()
                    if response.status_code != 200:
                        raise ScienceError(f'IRSA cutout returned HTTP {response.status_code}.')
                    parts = []
                    total = 0
                    for chunk in response.iter_bytes():
                        total += len(chunk)
                        if total > MAX_CUTOUT_BYTES:
                            raise ScienceError('Cutout exceeds the current preview size limit. Try a smaller field.')
                        parts.append(chunk)
                    return b''.join(parts)
        except httpx.HTTPError as exc:
            last_exc = exc
            time.sleep(2.0 * (attempt + 1))
    raise ScienceError(f'IRSA cutout download failed: {type(last_exc).__name__}') from last_exc


def reference_wcs(ra: float, dec: float, fov_arcmin: float):
    from astropy.wcs import WCS
    pix_scale_arcsec = 6.2  # display sampling, not a claimed instrument resolution
    n = int(np.clip(math.ceil(fov_arcmin * 60 / pix_scale_arcsec), 48, 350))
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [(n + 1)/2, (n + 1)/2]
    wcs.wcs.cdelt = [-pix_scale_arcsec / 3600, pix_scale_arcsec / 3600]
    wcs.wcs.crval = [ra, dec]
    wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    return wcs, (n, n)


def local_wavelength(header, wcs_wave_table, src_wcs, ra: float, dec: float) -> dict:
    """Central wavelength/bandwidth at a sky position via the file's spectral WCS.

    Uses the alternate LINEAR 'A' WCS ("0-based active pixel coordinates")
    carried in IRSA cutouts to map the target pixel back to the original
    detector grid, then bilinearly interpolates the 9x9 WCS-WAVE lookup grid.
    Visualization-grade per the explanatory supplement; not survey-grade
    spectral WCS.
    """
    try:
        x0, y0 = (float(v) for v in src_wcs.all_world2pix(ra, dec, 0))
        crpix1a = float(header.get('CRPIX1A'))
        crpix2a = float(header.get('CRPIX2A'))
        record = wcs_wave_table if hasattr(wcs_wave_table, 'keys') else wcs_wave_table[0]
        grid_x = np.asarray(record['X'], dtype=float)   # 1-based active-pixel columns
        grid_y = np.asarray(record['Y'], dtype=float)
        values = np.asarray(record['VALUES'], dtype=float)
        # Real files store (9, 9, 2) = [lambda, bandwidth] per node; be liberal.
        if values.ndim == 3 and values.shape[-1] == 2:
            lam_grid, bw_grid = values[..., 0], values[..., 1]
        elif values.ndim == 3 and values.shape[0] == 2:
            lam_grid, bw_grid = values[0], values[1]
        else:
            return {'lambda_um': None, 'bandwidth_um': None,
                    'reason': f'unexpected WCS-WAVE VALUES shape {values.shape}'}
        # Convert lookup grid to the same 0-based active-pixel frame.
        det_x = (x0 + 1 - crpix1a)  # CDELT=1, CRVAL=0 for the 'A' WCS
        det_y = (y0 + 1 - crpix2a)
        gx0, gy0 = grid_x - 1.0, grid_y - 1.0
        if not (gx0.min() <= det_x <= gx0.max() and gy0.min() <= det_y <= gy0.max()):
            return {'lambda_um': None, 'bandwidth_um': None,
                    'reason': 'target position outside the spectral WCS grid'}
        i = int(np.clip(np.searchsorted(gx0, det_x) - 1, 0, len(gx0) - 2))
        j = int(np.clip(np.searchsorted(gy0, det_y) - 1, 0, len(gy0) - 2))
        tx = (det_x - gx0[i]) / (gx0[i + 1] - gx0[i])
        ty = (det_y - gy0[j]) / (gy0[j + 1] - gy0[j])
        lam = float((lam_grid[j, i] * (1 - tx) * (1 - ty) + lam_grid[j, i + 1] * tx * (1 - ty)
                     + lam_grid[j + 1, i] * (1 - tx) * ty + lam_grid[j + 1, i + 1] * tx * ty))
        bw = float((bw_grid[j, i] * (1 - tx) * (1 - ty) + bw_grid[j, i + 1] * tx * (1 - ty)
                    + bw_grid[j + 1, i] * (1 - tx) * ty + bw_grid[j + 1, i + 1] * tx * ty))
        return {'lambda_um': round(lam, 4), 'bandwidth_um': round(bw, 4), 'reason': 'ok'}
    except ScienceError:
        raise
    except Exception as exc:  # header layout differences must not kill rendering
        return {'lambda_um': None, 'bandwidth_um': None,
                'reason': f'spectral WCS unavailable ({type(exc).__name__})'}


def open_cutout(source: str, ra: float, dec: float, fov_arcmin: float):
    """Open the downloaded cutout and return the science products we use."""
    from astropy.io import fits
    from astropy.wcs import WCS
    file_bytes = get_cutout_bytes(source, ra, dec, fov_arcmin)
    try:
        hdul = fits.open(io.BytesIO(file_bytes), memmap=False, lazy_load_hdus=False)
    except (OSError, ValueError) as exc:
        raise ScienceError(f'Cannot read IRSA FITS cutout: {type(exc).__name__}') from exc
    try:
        sci = hdul[1]
        data = np.asarray(sci.data, dtype=np.float64)
        if data.ndim != 2:
            raise ScienceError(f'Expected a 2-D SPHEREx spectral image; received {data.ndim} dimensions.')
        src_wcs = WCS(sci.header).celestial
        flags = np.asarray(hdul[2].data) if len(hdul) > 2 and hdul[2].data is not None else None
        variance = (np.asarray(hdul[3].data, dtype=np.float64)
                    if len(hdul) > 3 and hdul[3].data is not None else None)
        zodi = (np.asarray(hdul[4].data, dtype=np.float64)
                if len(hdul) > 4 and hdul[4].data is not None else None)
        wave_hdu = next((h for h in hdul if h.name == 'WCS-WAVE'), None)
        return {'header': sci.header, 'data': data, 'wcs': src_wcs, 'flags': flags,
                'variance': variance, 'zodi': zodi, 'wave_table': wave_hdu.data if wave_hdu else None,
                'hdul': hdul}
    except Exception:
        hdul.close()
        raise


@lru_cache(maxsize=24)
def aligned_frame(source: str, ra: float, dec: float, fov_arcmin: float,
                  mask_level: str = 'display'):
    """Reproject the science plane into an identical tangent-plane pixel grid.

    Masking follows the official flag-bit semantics: only fatal status bits
    invalidate a pixel.  SOURCE-flagged pixels (bit 21) carry the flux of real
    sources and stay visible.  mask_level='display' additionally keeps
    saturated cores visible; 'strict' (photometry) masks them.
    """
    from reproject import reproject_interp
    products = open_cutout(source, ra, dec, fov_arcmin)
    hdul = products['hdul']
    try:
        data, src_wcs = products['data'], products['wcs']
        valid = np.isfinite(data)
        flag_summary = None
        if products['flags'] is not None and products['flags'].shape == data.shape:
            flag_summary = summarize_flags(products['flags'])
            valid &= ~fatal_mask(products['flags'], mask_level)
        clean = np.where(valid, data, np.nan)
        bunit = str(products['header'].get('BUNIT', 'unspecified')).strip()
        image, footprint = reproject_interp((clean, src_wcs), *reference_wcs(ra, dec, fov_arcmin),
                                            return_footprint=True)
        image = np.where((footprint > 0) & np.isfinite(image), image, np.nan)
        meta = {'bunit': bunit, 'flag_summary': flag_summary,
                'flagged_input_fraction': flag_summary['fatal_fraction'] if flag_summary else None,
                'source_flag_fraction': flag_summary['source_flag_fraction'] if flag_summary else None,
                'valid_output_fraction': float(np.isfinite(image).mean()),
                'processing': 'WCS reprojection (interpolated; visual preview)',
                'source_url': source}
        var_med = products['variance']
        meta['median_variance'] = (float(np.nanmedian(var_med[valid])) if var_med is not None
                                   and var_med.shape == data.shape and valid.any() else None)
        zodi_med = products['zodi']
        meta['zodi_median'] = (float(np.nanmedian(zodi_med[valid])) if zodi_med is not None
                               and zodi_med.shape == data.shape and valid.any() else None)
        if products['wave_table'] is not None:
            wave = local_wavelength(products['header'], products['wave_table'], src_wcs, ra, dec)
            meta['wavelength_local_um'] = wave['lambda_um']
            meta['bandwidth_local_um'] = wave['bandwidth_um']
            meta['wavelength_note'] = wave['reason']
        else:
            meta['wavelength_local_um'] = meta['bandwidth_local_um'] = None
            meta['wavelength_note'] = 'no WCS-WAVE table in cutout'
        return image, meta
    finally:
        hdul.close()


def robust_stretch(a: np.ndarray, b: np.ndarray | None = None, *additional: np.ndarray):
    """One shared display stretch for all selected dates (not calibrated photometry)."""
    values = np.concatenate([arr[np.isfinite(arr)] for arr in (a, b, *additional) if arr is not None])
    if not len(values):
        raise ScienceError('No unflagged overlapping pixels in this field; select another exposure.')
    lo, hi = np.percentile(values, [1, 99.5])
    if not np.isfinite(hi-lo) or hi <= lo:
        lo = float(np.nanmin(values)); hi = float(np.nanmax(values))
    if hi <= lo: hi = lo + 1
    return float(lo), float(hi)


def residual_regions(a: np.ndarray, b: np.ndarray, limit: int = 6):
    """Return review cues for strong residual regions, never a discovery score.

    This deliberately uses a simple, auditable threshold and reports regions in
    display-pixel coordinates only.  It is a triage aid for human inspection;
    it is not a motion classifier and has no statistical significance model.
    """
    valid = np.isfinite(a) & np.isfinite(b)
    if not np.any(valid):
        return []
    aa = a - np.nanmedian(a)
    bb = b - np.nanmedian(b)
    delta = bb - aa
    absolute = np.abs(delta[valid])
    threshold = float(np.percentile(absolute, 99.0)) if absolute.size else 0.0
    if not np.isfinite(threshold) or threshold <= 0:
        return []
    mask = valid & (np.abs(delta) >= threshold)
    # Connected components are intentionally 8-connected and dependency-free.
    visited = np.zeros(mask.shape, dtype=bool)
    regions = []
    h, w = mask.shape
    for y, x in zip(*np.where(mask)):
        if visited[y, x]:
            continue
        stack = [(int(y), int(x))]
        visited[y, x] = True
        points = []
        while stack:
            cy, cx = stack.pop(); points.append((cy, cx))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True; stack.append((ny, nx))
        if len(points) < 2:
            continue
        ys = np.array([p[0] for p in points], dtype=float)
        xs = np.array([p[1] for p in points], dtype=float)
        vals = delta[ys.astype(int), xs.astype(int)]
        regions.append({'x_pixel': round(float(xs.mean()), 2),
                        'y_pixel': round(float(ys.mean()), 2),
                        'pixels': int(len(points)),
                        'peak_abs_residual': round(float(np.max(np.abs(vals))), 6),
                        'sign': 'B brighter' if float(np.mean(vals)) >= 0 else 'A brighter'})
    return sorted(regions, key=lambda item: (-item['pixels'], -item['peak_abs_residual']))[:limit]


def to_png(a: np.ndarray, b: np.ndarray | None, mode: str,
           stretch: tuple[float, float] | None = None):
    if mode in ('a', 'b', 'mean'):
        lo, hi = stretch if stretch is not None else robust_stretch(a, b)
        arr = a if mode == 'a' else b if mode == 'b' else np.nanmean(np.stack((a, b)), axis=0)
        # Common stretch across A and B prevents automatic per-epoch contrast from masking variability.
        scaled = np.clip((arr - lo) / (hi - lo), 0, 1)
        intensity = np.uint8(np.nan_to_num(np.arcsinh(9*scaled) / np.arcsinh(9)) * 255)
        rgba = np.stack((intensity, intensity, intensity,
                         np.where(np.isfinite(arr), 255, 0).astype('uint8')), axis=2)
    elif mode == 'difference':
        if b is None:
            raise ScienceError('Choose two observations for difference mode.')
        valid = np.isfinite(a) & np.isfinite(b)
        aa = a - np.nanmedian(a); bb = b - np.nanmedian(b)
        delta = bb - aa
        values = np.abs(delta[valid])
        if values.size == 0:
            raise ScienceError('No overlapping valid pixels in the chosen exposures.')
        high = float(np.percentile(values, 98))
        if high <= 0: high = 1
        intensity = np.uint8(np.clip(np.abs(delta) / high, 0, 1)**0.7 * 255)
        pos = delta >= 0
        # Amber = B brighter; cyan = A brighter. Transparent = invalid coverage.
        r = np.where(pos, intensity, intensity * 0.18).astype('uint8')
        g = np.where(pos, intensity * 0.66, intensity * 0.77).astype('uint8')
        bl = np.where(pos, intensity * 0.2, intensity).astype('uint8')
        rgba = np.stack((r, g, bl, np.where(valid, 255, 0).astype('uint8')), axis=2)
    else:
        raise ScienceError('Unsupported rendering mode.')
    buffer = io.BytesIO()
    # Array +Y is upward per celestial WCS. Canvas/Y is downward; flip to show north up.
    Image.fromarray(np.flipud(rgba), mode='RGBA').save(buffer, format='PNG')
    return buffer.getvalue()


def wavelength_match_warning(meta_a: dict, meta_b: dict | None) -> dict | None:
    """Compare the local wavelengths of two epochs at the target position."""
    la, lb = meta_a.get('wavelength_local_um'), (meta_b or {}).get('wavelength_local_um')
    if la is None or lb is None:
        return {'status': 'unknown', 'delta_um': None,
                'note': 'Local wavelength could not be determined for at least one epoch.'}
    delta = round(abs(la - lb), 4)
    return {'status': 'matched' if delta <= 0.03 else 'mismatched', 'delta_um': delta,
            'a_um': la, 'b_um': lb,
            'note': ('Local wavelength matched at the target within 0.03 um.'
                     if delta <= 0.03 else
                     'Local wavelengths at the target differ by more than 0.03 um; '
                     'the difference image mixes different bands of the variable filter.')}


def render_pair(source_a: str, source_b: str | None, ra: float, dec: float, fov: float, mode: str):
    # Difference photometry needs strict masking; visual modes keep saturated
    # star cores visible so bright sources do not become holes.
    level = 'strict' if mode == 'difference' else 'display'
    a, meta_a = aligned_frame(source_a, ra, dec, fov, level)
    b = meta_b = None
    if source_b:
        b, meta_b = aligned_frame(source_b, ra, dec, fov, level)
        if mode == 'difference' and meta_a['bunit'].lower() != meta_b['bunit'].lower():
            raise ScienceError('Cannot subtract images with different reported physical units.')
    if mode in ('b', 'mean', 'difference') and b is None:
        raise ScienceError('Choose a second observation.')
    regions = residual_regions(a, b) if b is not None else []
    _, (n_x, n_y) = reference_wcs(ra, dec, fov)
    match = wavelength_match_warning(meta_a, meta_b) if b is not None else None
    return to_png(a, b, mode), {'a': meta_a, 'b': meta_b,
                               'mask_level': level,
                               'wavelength_match': match,
                               'exploratory_residual_regions': regions,
                               'display_grid': {'width': n_x, 'height': n_y,
                                                'pixel_scale_arcsec': 6.2,
                                                'ra': ra, 'dec': dec,
                                                'crval': [ra, dec],
                                                'note': 'shared TAN display grid; +y is north'},
                               'residual_interpretation': ('Regions are percentile-thresholded visual review cues in display pixels; '
                                  'they are not detections, significance estimates, or measured motion.'),
                               'comparison_warning': ('Visual comparison only. Matching detector ranges does not guarantee '
                                  'identical per-pixel SPHEREx wavelengths, photometric scales or PSFs. '
                                  'Difference output is NOT a validated transient or moving-object detection.')}


def render_sequence(sources: Sequence[str], ra: float, dec: float, fov: float):
    """Render 2-8 real IRSA exposures using a *common* display intensity scale.

    Intended for movement/structure exploration only. Different local wavelengths,
    calibration, PSFs, and exposure backgrounds can mimic variability.
    """
    if not 2 <= len(sources) <= 8:
        raise ScienceError('Select 2-8 different archive observations for a time sequence.')
    if len(set(sources)) != len(sources):
        raise ScienceError('Duplicate observations are not allowed in a sequence.')
    frames, metadata = [], []
    for source in sources:
        img, meta = aligned_frame(source, ra, dec, fov, 'display')
        frames.append(img)
        metadata.append(meta)
    units = {(item.get('bunit') or '').strip().lower() for item in metadata}
    if len(units) != 1:
        raise ScienceError('Exposures report different physical units. Cannot use one shared brightness scale.')
    lo, hi = robust_stretch(frames[0], frames[1], *frames[2:])
    _, (n_x, n_y) = reference_wcs(ra, dec, fov)
    return [to_png(frame, None, 'a', stretch=(lo, hi)) for frame in frames], {
        'frames': metadata, 'display_stretch': {'low': lo, 'high': hi},
        'display_grid': {'width': n_x, 'height': n_y, 'pixel_scale_arcsec': 6.2,
                         'crval': [ra, dec], 'note': 'shared TAN display grid; +y is north'},
        'comparison_warning': ('All frames share one asinh intensity stretch and common WCS TAN display grid. '
            'Wavelengths, PSFs, exposure backgrounds, and calibration can differ. '
            'The sequence is not a verified flux measurement, moving-object identification, or discovery.'),
        'scientific_level': 'exploratory_previews_only',
    }
