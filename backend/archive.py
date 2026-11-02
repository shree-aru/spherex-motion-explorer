"""Small, transparent adapter for the official IRSA SIA v2 archive."""
from __future__ import annotations

import csv
import hashlib
import io
import math
import time
from datetime import datetime, timedelta, timezone, date
from urllib.parse import urlsplit

import httpx

SIA_URL = "https://irsa.ipac.caltech.edu/SIA"
RELEASES = {"qr3": "spherex_qr3", "qr2": "spherex_qr2"}
SURVEYS = {"wide", "deep"}
DETECTOR_BANDS = {
    "D1": (0.75, 1.09), "D2": (1.10, 1.62), "D3": (1.63, 2.41),
    "D4": (2.42, 3.82), "D5": (3.83, 4.41), "D6": (4.42, 5.00),
}
MJD_ZERO = datetime(1858, 11, 17, tzinfo=timezone.utc)


class ArchiveError(Exception):
    pass


def valid_source_url(source: str) -> bool:
    """Block SSRF: only on-prem SPHEREx FITS files at IRSA may be downloaded."""
    try:
        parts = urlsplit(source)
        return (parts.scheme == "https"
                and parts.hostname == "irsa.ipac.caltech.edu"
                and parts.port is None
                and parts.path.startswith("/ibe/data/spherex/")
                and parts.path.lower().endswith((".fits", ".fits.gz"))
                and not parts.username and not parts.password
                and not parts.query and not parts.fragment)
    except (ValueError, TypeError):
        return False


def metadata_number(row: dict, name: str) -> float | None:
    try:
        value = float(row.get(name) or "")
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


def band_for_range(lo: float | None, hi: float | None) -> str:
    if lo is None or hi is None:
        return "Unknown"
    mid = (lo + hi) / 2
    for name, (left, right) in DETECTOR_BANDS.items():
        if left <= mid <= right:
            return name
    return "Unknown"


def iso_from_mjd(mjd: float | None) -> str | None:
    if mjd is None:
        return None
    try:
        return (MJD_ZERO + timedelta(days=mjd)).isoformat().replace('+00:00', 'Z')
    except OverflowError:
        return None


def angular_separation_arcmin(ra1: float, dec1: float, ra2: float, dec2: float) -> float | None:
    """Great-circle separation in arcminutes (haversine, small-angle safe)."""
    try:
        r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
        hav = (math.sin((d2 - d1) / 2) ** 2
               + math.cos(d1) * math.cos(d2) * math.sin((r2 - r1) / 2) ** 2)
        return round(math.degrees(2 * math.asin(min(1.0, math.sqrt(hav)))) * 60, 4)
    except (ValueError, TypeError):
        return None


def parse_sia_csv(contents: str, release: str, ra: float | None = None,
                  dec: float | None = None) -> list[dict]:
    rows = []
    for row in csv.DictReader(io.StringIO(contents.lstrip('\ufeff'))):
        source = (row.get('access_url') or '').strip()
        if not valid_source_url(source):
            continue  # SIA may return non-FITS side products or cloud paths.
        lo = metadata_number(row, 'em_min')
        hi = metadata_number(row, 'em_max')
        if lo is not None: lo *= 1_000_000
        if hi is not None: hi *= 1_000_000
        t_min = metadata_number(row, 't_min')
        t_max = metadata_number(row, 't_max')
        s_ra = metadata_number(row, 's_ra')
        s_dec = metadata_number(row, 's_dec')
        separation = (angular_separation_arcmin(ra, dec, s_ra, s_dec)
                      if ra is not None and dec is not None and s_ra is not None and s_dec is not None
                      else None)
        rows.append({
            'id': hashlib.sha256(source.encode('utf8')).hexdigest()[:18],
            'source': source,
            'obs_id': row.get('obs_id') or row.get('obs_publisher_did') or 'Not supplied',
            'date_utc': iso_from_mjd(t_min),
            'date_end_utc': iso_from_mjd(t_max),
            'band': band_for_range(lo, hi),
            'wavelength_min_um': round(lo, 4) if lo is not None else None,
            'wavelength_max_um': round(hi, 4) if hi is not None else None,
            'center_offset_arcmin': separation,
            'release': release.upper(),
            'instrument': row.get('instrument_name') or 'SPHEREx',
        })
    return sorted(rows, key=lambda item: (item['date_utc'] or '', item['band'], item['id']))


def mjd_from_date(value: date) -> float:
    """Midnight UTC of a given calendar date, in Modified Julian Days."""
    return (datetime(value.year, value.month, value.day, tzinfo=timezone.utc) - MJD_ZERO).total_seconds() / 86400


def search_observations(ra: float, dec: float, fov_arcmin: float, release: str = 'qr3',
                        maxrec: int = 600, start_date: date | None = None,
                        end_date: date | None = None, survey: str = 'wide'):
    if release not in RELEASES:
        raise ValueError('Unsupported SPHEREx release.')
    if survey not in SURVEYS:
        raise ValueError('Unsupported SPHEREx survey.')
    radius_deg = max(0.005, (fov_arcmin / 60) * 2**0.5 / 2)
    if start_date and end_date and start_date > end_date:
        raise ValueError('Start date cannot be after the end date.')
    params = {
        'COLLECTION': RELEASES[release] + ('_deep' if survey == 'deep' else ''),
        'POS': f'CIRCLE {ra:.8f} {dec:.8f} {radius_deg:.8f}',
        'RESPONSEFORMAT': 'CSV', 'MAXREC': str(maxrec), 'CALIB': '2', 'DPTYPE': 'image',
    }
    if start_date or end_date:
        # SIA TIME is inclusive and MJD-based, so end date covers that UTC day.
        lo = f'{mjd_from_date(start_date):.5f}' if start_date else '-Inf'
        hi = f'{mjd_from_date(end_date + timedelta(days=1)):.5f}' if end_date else '+Inf'
        params['TIME'] = f'{lo} {hi}'
    last_exc = None
    payload = None
    for attempt in range(3):  # the IRSA route can stall; retry with backoff
        try:
            with httpx.Client(timeout=httpx.Timeout(45.0 if attempt else 38.0, connect=10.0),
                              follow_redirects=False) as client:
                response = client.get(SIA_URL, params=params)
                response.raise_for_status()
                payload = response.text
            break
        except httpx.HTTPError as exc:
            last_exc = exc
            time.sleep(2.0 * (attempt + 1))
    if payload is None:
        raise ArchiveError(f'IRSA SIA service is unreachable: {type(last_exc).__name__}') from last_exc
    header = next(csv.reader(io.StringIO(payload.lstrip('\ufeff'))), [])
    if 'access_url' not in header:
        raise ArchiveError('IRSA did not return a recognised SIA CSV response; verify the selected collection and archive availability.')
    results = parse_sia_csv(payload, release, ra=ra, dec=dec)
    dated = [item for item in results if item['date_utc']]
    earliest = min((item['date_utc'] for item in dated), default=None)
    latest = max((item['date_utc'] for item in dated), default=None)
    baseline_days = None
    if earliest and latest:
        first = datetime.fromisoformat(earliest.replace('Z', '+00:00'))
        last = datetime.fromisoformat(latest.replace('Z', '+00:00'))
        baseline_days = round((last - first).total_seconds() / 86400, 3)
    return {'observations': results, 'archive_count': len(results),
            'result_limit': maxrec, 'may_be_truncated': len(list(csv.DictReader(io.StringIO(payload)))) >= maxrec,
            'query_url': str(httpx.URL(SIA_URL, params=params)),
            'coverage': {'earliest_utc': earliest, 'latest_utc': latest,
                         'baseline_days': baseline_days,
                         'dated_records': len(dated),
                         'recommended_action': ('Choose the earliest and latest compatible epochs for an exploratory comparison.'
                                                if baseline_days and baseline_days > 0 else
                                                'No multi-epoch baseline was found in this response; widen the query or try another release.')},
            'survey': survey,
            'time_filter': {'start_utc': str(start_date) if start_date else None,
                            'end_utc': str(end_date) if end_date else None},
            'note': ('SIA returns intersecting exposures, not guaranteed full coverage of the requested field. '
                     'Detector bands are inferred from file-level wavelength ranges and are not per-pixel wavelength matching.')}
