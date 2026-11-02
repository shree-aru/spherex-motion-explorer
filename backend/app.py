"""SPHEREx Motion Explorer public API + local front end."""
from __future__ import annotations

import base64
import json
import math
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles

from .archive import ArchiveError, search_observations, valid_source_url, DETECTOR_BANDS
from .science import ScienceError, render_pair, render_sequence
from .spectrum import extract_spectrum
from .catalog import CatalogError, gaia_sources
from .atlas import AtlasError, atlas_fits

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title='SPHEREx Motion Explorer', version='0.5.0',
              description='Official IRSA query and WCS-aligned exploratory visualization; not a discovery certification system.')


def validate_coords(ra: float, dec: float, fov: float):
    if not (math.isfinite(ra) and 0 <= ra < 360 and math.isfinite(dec) and -90 <= dec <= 90):
        raise HTTPException(422, 'RA must be 0–360° (exclusive); declination must be −90–90°.')
    if not (math.isfinite(fov) and 1 <= fov <= 18):
        raise HTTPException(422, 'Field of view must be between 1 and 18 arcminutes in this preview.')


def decode_source(token: str):
    try:
        raw = base64.urlsafe_b64decode(token + '=' * (-len(token) % 4)).decode('utf8')
    except (ValueError, UnicodeError) as exc:
        raise HTTPException(422, 'Invalid observation source token.') from exc
    if not valid_source_url(raw):
        raise HTTPException(422, 'Invalid or untrusted observation source URL.')
    return raw


@app.get('/api/health')
def health():
    try:
        import astropy, reproject
        scientific_engine = 'available'
    except ImportError:
        scientific_engine = 'dependencies_missing'
    return {'service': 'SPHEREx Motion Explorer', 'version': '0.5.0',
            'archive': 'NASA/IPAC IRSA SIA v2', 'scientific_engine': scientific_engine,
            'data_policy': 'real_archive_only', 'status': 'online'}


@app.get('/api/observations')
def observations(ra: float, dec: float, fov: float = 4.0,
                 release: Literal['qr3', 'qr2'] = 'qr3',
                 start_date: date | None = None, end_date: date | None = None,
                 survey: Literal['wide', 'deep'] = 'wide'):
    validate_coords(ra, dec, fov)
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, 'Start date must be on or before end date.')
    try:
        result = search_observations(ra, dec, fov, release=release,
                                     start_date=start_date, end_date=end_date, survey=survey)
        for row in result['observations']:
            source = row.pop('source')
            row['token'] = base64.urlsafe_b64encode(source.encode('utf8')).decode().rstrip('=')
        return result
    except ArchiveError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.get('/api/render')
def render(ra: float, dec: float, fov: float,
           a: str = Query(..., min_length=10), b: str | None = None,
           mode: Literal['a', 'b', 'mean', 'difference'] = 'a'):
    validate_coords(ra, dec, fov)
    try:
        img, meta = render_pair(decode_source(a), decode_source(b) if b else None,
                                round(ra, 8), round(dec, 8), round(fov, 5), mode)
        meta64 = base64.urlsafe_b64encode(json.dumps(meta).encode()).decode()
        # Same-origin browser can inspect provenance; FITS input is never silently replaced.
        return Response(img, media_type='image/png', headers={
            'Cache-Control': 'private, max-age=600',
            'X-Science-Metadata': meta64,
            'X-Image-Mode': mode,
            'X-Data-Source': 'NASA-IPAC-IRSA-SPHEREx',
        })
    except ScienceError as exc:
        raise HTTPException(422, str(exc)) from exc


class SequenceRequest(BaseModel):
    ra: float
    dec: float
    fov: float
    tokens: list[str] = Field(min_length=2, max_length=8)


@app.post('/api/sequence')
def sequence(body: SequenceRequest):
    """2–8 real observations registered and rendered at a common display stretch."""
    validate_coords(body.ra, body.dec, body.fov)
    if any(len(token) > 4096 for token in body.tokens):
        raise HTTPException(422, 'Observation tokens exceed permitted length.')
    sources = [decode_source(token) for token in body.tokens]
    try:
        pngs, meta = render_sequence(sources, round(body.ra, 8), round(body.dec, 8),
                                     round(body.fov, 5))
    except ScienceError as exc:
        raise HTTPException(422, str(exc)) from exc
    return Response(
        content=json.dumps({'images_base64': [base64.b64encode(png).decode('ascii') for png in pngs],
                            'metadata': meta}),
        media_type='application/json',
        headers={'Cache-Control': 'private, max-age=300', 'X-Data-Source': 'NASA-IPAC-IRSA-SPHEREx'},
    )


@app.get('/api/spectrum')
def spectrum(ra: float, dec: float, fov: float = 4.0,
             release: Literal['qr3', 'qr2'] = 'qr3',
             start_date: date | None = None, end_date: date | None = None,
             survey: Literal['wide', 'deep'] = 'wide',
             max_files: int = Query(40, ge=4, le=60)):
    """Exploratory on-the-fly spectrophotometry from many real archive files."""
    validate_coords(ra, dec, fov)
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, 'Start date must be on or before end date.')
    try:
        found = search_observations(ra, dec, fov, release=release, start_date=start_date,
                                    end_date=end_date, survey=survey)
        result = extract_spectrum(ra, dec, fov, found['observations'], max_files=max_files)
    except ArchiveError as exc:
        raise HTTPException(502, str(exc)) from exc
    except ScienceError as exc:
        raise HTTPException(422, str(exc)) from exc
    result.update({'ra': ra, 'dec': dec, 'release': release.upper(), 'survey': survey,
                   'archive_count': found['archive_count'],
                   'query_url': found['query_url'],
                   'disclaimer': ('Exploratory visualization product; not calibrated '
                                  'spectrophotometry and not a discovery claim.')})
    return JSONResponse(content=result, headers={'Cache-Control': 'private, max-age=600',
                                                 'X-Data-Source': 'NASA-IPAC-IRSA-SPHEREx'})


@app.get('/api/catalog')
def catalog(ra: float, dec: float, fov: float = 9.0, survey: Literal['gaia'] = 'gaia',
            mag_limit: float = Query(17.5, ge=5, le=22), epoch: float | None = None):
    """Reference-star overlay positions (Gaia DR3 via IRSA TAP), epoch-propagated."""
    validate_coords(ra, dec, fov)
    try:
        result = gaia_sources(ra, dec, fov, mag_limit=mag_limit, epoch=epoch)
    except CatalogError as exc:
        raise HTTPException(502, str(exc)) from exc
    return JSONResponse(content=result, headers={'Cache-Control': 'private, max-age=1800',
                                                 'X-Data-Source': 'IRSA-TAP-Gaia-DR3'})


@app.get('/api/atlas_image')
def atlas_image(ra: float, dec: float, fov: float = 9.0,
                ref: Literal['wise', '2mass'] = 'wise'):
    """Compact WCS-aligned reference FITS (IRSA AllWISE/2MASS atlas) for the atlas view."""
    validate_coords(ra, dec, fov)
    try:
        payload = atlas_fits(round(ra, 6), round(dec, 6), round(fov, 4), ref)
    except AtlasError as exc:
        raise HTTPException(503, str(exc)) from exc
    return Response(payload, media_type='application/fits',
                    headers={'Cache-Control': 'private, max-age=86400',
                             'X-Data-Source': f'NASA-IPAC-IRSA-{ref.upper()}-ATLAS'})


app.mount('/', StaticFiles(directory=ROOT / 'frontend', html=True), name='frontend')
