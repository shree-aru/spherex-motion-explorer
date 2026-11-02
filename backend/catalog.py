"""Reference catalogue overlay: Gaia DR3 positions epoch-propagated for context.

Positions are queried from the official IRSA TAP service and propagated from
the Gaia reference epoch (J2016.0) to the requested epoch using published
proper motions, so nearby-star motion is visible against SPHEREx frames.
This is context overlay only, not a cross-identification or detection service.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

import httpx

TAP_URL = 'https://irsa.ipac.caltech.edu/TAP/sync'
GAIA_TABLE = 'gaia_dr3_source'
GAIA_EPOCH = 2016.0


class CatalogError(Exception):
    pass


def current_epoch_year() -> float:
    now = datetime.now(timezone.utc)
    start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    return now.year + (now - start).total_seconds() / (86400 * 365.25)


def mjd_to_epoch_year(mjd: float) -> float:
    return 2000.0 + (mjd - 51544.5) / 365.25


def propagate(ra_deg: float, dec_deg: float, pmra: float | None, pmdec: float | None,
              ref_epoch: float, target_epoch: float) -> tuple[float, float]:
    """First-order proper-motion propagation (no parallax or radial velocity)."""
    if pmra is None or pmdec is None:
        return ra_deg, dec_deg
    dt = target_epoch - ref_epoch
    dec_rad = __import__('math').radians(dec_deg)
    ra_p = ra_deg + (pmra / 3_600_000.0) * dt / max(0.01, __import__('math').cos(dec_rad))
    dec_p = dec_deg + (pmdec / 3_600_000.0) * dt
    return ra_p % 360.0, max(-90.0, min(90.0, dec_p))


def gaia_sources(ra: float, dec: float, radius_arcmin: float, limit: int = 300,
                 mag_limit: float = 17.5, epoch: float | None = None) -> dict:
    radius_deg = min(max(radius_arcmin / 60.0, 1.0 / 60), 1.0)
    limit = max(1, min(int(limit), 500))
    target_epoch = round(epoch if epoch is not None else current_epoch_year(), 3)
    query = (
        f"SELECT TOP {limit} source_id, ra, dec, pmra, pmdec, ref_epoch, "
        f"phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag "
        f"FROM {GAIA_TABLE} "
        f"WHERE CONTAINS(POINT('ICRS', ra, dec), "
        f"CIRCLE('ICRS', {ra:.8f}, {dec:.8f}, {radius_deg:.8f})) = 1 "
        f"AND phot_g_mean_mag < {mag_limit} "
        f"ORDER BY phot_g_mean_mag ASC"
    )
    params = {'REQUEST': 'doQuery', 'LANG': 'ADQL', 'FORMAT': 'csv', 'QUERY': query}
    last_exc = None
    for attempt in range(2):  # the IRSA route can stall; one retry
        try:
            with httpx.Client(timeout=httpx.Timeout(60.0, connect=15.0), follow_redirects=False) as client:
                response = client.get(TAP_URL, params=params)
                response.raise_for_status()
                payload = response.text
            break
        except httpx.HTTPError as exc:
            last_exc = exc
    else:
        raise CatalogError(f'IRSA TAP service unreachable: {type(last_exc).__name__}') from last_exc
    if '<VOTABLE' in payload[:200]:
        # IRSA reports TAP faults as VOTABLE INFO even with FORMAT=csv.
        marker = 'value="ERROR"'
        if marker in payload:
            start = payload.find(marker)
            excerpt = payload[start:payload.find('>', start + len(marker))].strip('">')
            raise CatalogError(f'IRSA TAP query rejected: {excerpt[:180]}')
    sources = []
    for row in csv.DictReader(io.StringIO(payload.lstrip('\ufeff'))):
        try:
            ra0, dec0 = float(row['ra']), float(row['dec'])
            pmra = float(row['pmra']) if row.get('pmra') not in (None, '', 'None') else None
            pmdec = float(row['pmdec']) if row.get('pmdec') not in (None, '', 'None') else None
            ref = float(row.get('ref_epoch') or GAIA_EPOCH)
            g = float(row['phot_g_mean_mag']) if row.get('phot_g_mean_mag') not in (None, '', 'None') else None
        except (ValueError, TypeError, KeyError):
            continue
        ra_p, dec_p = propagate(ra0, dec0, pmra, pmdec, ref, target_epoch)
        sources.append({
            'source_id': row.get('source_id'),
            'ra_epoch': round(ra0, 7), 'dec_epoch': round(dec0, 7),
            'ra_propagated': round(ra_p, 7), 'dec_propagated': round(dec_p, 7),
            'pmra_mas_yr': pmra, 'pmdec_mas_yr': pmdec,
            'ref_epoch': ref, 'g_mag': g,
            'motion_arcsec_yr': (round(((pmra**2 + pmdec**2) ** 0.5) / 1000.0, 4)
                                 if pmra is not None and pmdec is not None else None),
        })
    sources.sort(key=lambda s: (s['g_mag'] is None, s['g_mag'] if s['g_mag'] is not None else 99))
    return {'catalog': 'Gaia DR3 (IRSA TAP)', 'epoch_year': target_epoch,
            'requested_epoch_year': target_epoch,
            'count': len(sources), 'sources': sources,
            'note': ('Proper-motion propagated positions (no parallax/radial velocity). '
                     'Reference context only; not an identification of SPHEREx sources.')}
