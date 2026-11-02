"""Live end-to-end sweep against the running app + real IRSA data.

Run manually:  python tests/live_sweep.py  (server must be on 127.0.0.1:8000)
Not part of the offline pytest suite - this hits the live archive.
Prints a PASS/FAIL/WARN line per check and a summary at the end.
"""
import base64
import json
import sys
import time
import urllib.error
import urllib.request

BASE = 'http://127.0.0.1:8000'
TARGETS = {
    'barnard': (269.4521, 4.7706),  # epoch-2026 propagated (frontend does the same)
    'epsilon': (331.044, -56.783),
    'wise0855': (133.7577, -7.2422),  # epoch-2026 propagated
    'rw-aur': (76.957, 30.401),
    'r-dra': (248.168, 66.755),
}
results = []


def check(name, ok, detail='', warn=False):
    tag = 'PASS' if ok else ('WARN' if warn else 'FAIL')
    results.append((tag, name, detail))
    print(f'[{tag}] {name} - {detail}')
    return ok


def get(path, timeout=240):
    req = urllib.request.Request(BASE + path, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode())


def render_bytes(path, timeout=240):
    req = urllib.request.Request(BASE + path)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        import base64 as b64
        meta = r.headers.get('X-Science-Metadata')
        parsed = (json.loads(b64.urlsafe_b64decode(meta + '=' * (-len(meta) % 4)).decode()) if meta else {})
        return r.status, len(r.read()), parsed


print('=== 1. Health ===')
try:
    st, body = get('/api/health', 10)
    check('health endpoint', st == 200 and body.get('scientific_engine') == 'available', str(body)[:90])
except Exception as e:
    check('health endpoint', False, str(e)[:120])
    print('Server unreachable - aborting sweep.')
    sys.exit(1)

print('=== 2. Observation discovery - all five challenge targets ===')
target_obs = {}
target_release = {}
for name, (ra, dec) in TARGETS.items():
    t0 = time.time()
    release_used = 'qr3'
    try:
        st, d = get(f'/api/observations?ra={ra}&dec={dec}&fov=9&release=qr3&survey=wide', 240)
        if st == 200 and d['archive_count'] == 0:
            release_used = 'qr2'  # mirror the app's automatic QR3->QR2 fallback
            st, d = get(f'/api/observations?ra={ra}&dec={dec}&fov=9&release=qr2&survey=wide', 240)
        n = d['archive_count']
        cov = d['coverage']
        bands = len({o['band'] for o in d['observations']})
        interior = sum(1 for o in d['observations']
                       if o.get('center_offset_arcmin') is not None and o['center_offset_arcmin'] < 90)
        ok = st == 200 and n > 0 and bands >= 3 and (cov.get('baseline_days') or 0) > 1
        check(f'observations {name}', ok,
              f'{release_used.upper()}: {n} records, {bands} detectors, '
              f'baseline {cov.get("baseline_days")}d, {interior} target-centred, {time.time()-t0:.0f}s',
              warn=(n > 0 and bands < 3) or release_used == 'qr2')
        target_obs[name] = d['observations']
        target_release[name] = release_used
    except Exception as e:
        check(f'observations {name}', False, str(e)[:150])
        target_obs[name] = []
        target_release[name] = release_used


def pick_pair(obs, band=None, min_baseline_days=1.0):
    pool = [o for o in obs if o.get('date_utc') and o.get('token')
            and (o.get('center_offset_arcmin') or 999) < 90
            and (band is None or o['band'] == band)]
    pool.sort(key=lambda o: o['date_utc'])
    best = None
    for band_name in sorted({o['band'] for o in pool}):
        b = [o for o in pool if o['band'] == band_name]
        if len(b) >= 2:
            days = (time.mktime(time.strptime(b[-1]['date_utc'][:10], '%Y-%m-%d'))
                    - time.mktime(time.strptime(b[0]['date_utc'][:10], '%Y-%m-%d'))) / 86400
            if best is None or days > best[2]:
                best = (b[0], b[-1], days)
    if best and best[2] >= min_baseline_days:
        return best[0], best[1], best[2]
    return None


print('=== 3. A/B difference rendering per target ===')
for name, obs in target_obs.items():
    if not obs:
        check(f'render {name}', False, 'no observations', warn=True)
        continue
    pair = pick_pair(obs)
    if not pair:
        check(f'render {name}', False, 'no same-band interior pair', warn=True)
        continue
    a, b, days = pair
    try:
        st, size, meta = render_bytes(
            f"/api/render?ra={TARGETS[name][0]}&dec={TARGETS[name][1]}&fov=9"
            f"&mode=difference&a={a['token']}&b={b['token']}")
        valid = round(meta.get('a', {}).get('valid_output_fraction', 0), 3)
        lam_a = meta.get('a', {}).get('wavelength_local_um')
        lam_b = meta.get('b', {}).get('wavelength_local_um')
        regions = len(meta.get('exploratory_residual_regions', []))
        ok = st == 200 and size > 2000 and valid > 0.5
        detail = (f'{size}B, valid {valid:.0%}, baseline {days:.1f}d, '
                  f'local-lambda {lam_a}/{lam_b} um, {regions} residual cues')
        check(f'render {name}', ok, detail, warn=(valid < 0.8))
    except urllib.error.HTTPError as e:
        check(f'render {name}', False, f'HTTP {e.code}: {e.read().decode()[:100]}', warn=(e.code == 502))

print('=== 4. Sequence rendering (Barnard) ===')
obs = target_obs.get('barnard', [])
pool = sorted([o for o in obs if o.get('token') and (o.get('center_offset_arcmin') or 999) < 90
               and o['band'] == 'D3'], key=lambda o: o['date_utc'])
if len(pool) >= 3:
    tokens = [o['token'] for o in pool[:3]]
    body = json.dumps({'ra': TARGETS['barnard'][0], 'dec': TARGETS['barnard'][1],
                       'fov': 9, 'tokens': tokens}).encode()
    req = urllib.request.Request(BASE + '/api/sequence', data=body,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read().decode())
        frames = len(d.get('images_base64', []))
        stretches = d.get('metadata', {}).get('display_stretch', {})
        ok = frames == 3 and stretches.get('high', 0) > stretches.get('low', 0)
        check('sequence render', ok, f'{frames} frames, shared stretch {stretches}')
    except Exception as e:
        check('sequence render', False, str(e)[:120])
else:
    check('sequence render', False, 'insufficient centred D3 frames', warn=True)

print('=== 5. Spectrum extraction (Barnard, fast sweep) ===')
ra, dec = TARGETS['barnard']
t0 = time.time()
try:
    st, d = get(f'/api/spectrum?ra={ra}&dec={dec}&fov=4&release=qr3&survey=wide&max_files=8', 420)
    pts = d.get('points', [])
    lam_span = (pts[0]['lambda_um'], pts[-1]['lambda_um']) if pts else (None, None)
    snrs = [p.get('snr') or 0 for p in pts]
    ok = st == 200 and len(pts) >= 4 and max(snrs) > 5
    check('spectrum barnard', ok,
          f'{len(pts)} points, lambda {lam_span[0]}-{lam_span[1]} um, max SNR {max(snrs) if snrs else 0:.0f}, '
          f'{time.time()-t0:.0f}s', warn=(len(pts) < 8))
except Exception as e:
    check('spectrum barnard', False, str(e)[:150])

print('=== 6. Gaia catalog overlay ===')
for name in ('barnard', 'epsilon'):
    ra, dec = TARGETS[name]
    try:
        st, d = get(f'/api/catalog?ra={ra}&dec={dec}&fov=9', 120)
        srcs = d.get('sources', [])
        movers = [s for s in srcs if (s.get('motion_arcsec_yr') or 0) > 1]
        ok = st == 200 and len(srcs) > 20
        check(f'catalog {name}', ok,
              f'{len(srcs)} stars, {len(movers)} with motion >1"/yr'
              + (f', fastest {movers[0]["motion_arcsec_yr"]}"/yr' if movers else ''))
    except Exception as e:
        check(f'catalog {name}', False, str(e)[:120])

print('=== 7. AllWISE reference atlas ===')
for name in ('barnard', 'epsilon'):
    ra, dec = TARGETS[name]
    try:
        req = urllib.request.Request(
            BASE + f'/api/atlas_image?ra={ra}&dec={dec}&fov=9&ref=wise&tier=detail')
        with urllib.request.urlopen(req, timeout=300) as r:
            data = r.read()
        ok = r.status == 200 and data[:6] == b'SIMPLE' and len(data) > 50000
        check(f'atlas {name}', ok, f'{len(data)//1024} KB FITS')
    except urllib.error.HTTPError as e:
        check(f'atlas {name}', False, f'HTTP {e.code}', warn=(e.code == 503))

print('=== 8. Input validation (must reject, no network) ===')
cases = [('/api/observations?ra=-5&dec=0', 'negative RA'),
         ('/api/observations?ra=15&dec=95', 'Dec out of range'),
         ('/api/observations?ra=15&dec=0&fov=40', 'FOV above cap')]
for path, label in cases:
    try:
        st, _ = get(path, 30)
        check(f'validation: {label}', False, f'accepted with HTTP {st}')
    except urllib.error.HTTPError as e:
        check(f'validation: {label}', e.code == 422, f'HTTP {e.code}')
bad_token = base64.urlsafe_b64encode(b'https://evil.example/x.fits').decode().rstrip('=')
try:
    st, size, _ = render_bytes(f'/api/render?ra=269&dec=4&fov=5&mode=a&a={bad_token}')
    check('validation: untrusted token', False, f'accepted ({size}B)')
except urllib.error.HTTPError as e:
    check('validation: untrusted token', e.code == 422, f'HTTP {e.code}')

print('=== 9. WISE 0855 proper-motion sanity ===')
ra, dec = TARGETS['wise0855']
obs = target_obs.get('wise0855', [])
if obs:
    offs = sorted(o['center_offset_arcmin'] for o in obs if o.get('center_offset_arcmin') is not None)
    check('wise0855 coverage', True,
          f'{len(obs)} records, off-axis {offs[0]:.0f}-{offs[-1]:.0f} arcmin '
          f'(J2000 label warns: 2.9"/yr x 26yr ~ 1.3\' drift)', warn=False)
else:
    check('wise0855 coverage', False, 'no records - target may sit outside QR3 windows', warn=True)

n_pass = sum(1 for t, _, _ in results if t == 'PASS')
n_warn = sum(1 for t, _, _ in results if t == 'WARN')
n_fail = sum(1 for t, _, _ in results if t == 'FAIL')
print(f'\n=== SWEEP SUMMARY: {n_pass} PASS, {n_warn} WARN, {n_fail} FAIL ===')
for t, name, detail in results:
    if t != 'PASS':
        print(f'  [{t}] {name}: {detail}')
sys.exit(1 if n_fail else 0)
