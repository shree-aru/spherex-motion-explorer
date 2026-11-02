# SPHEREx Motion Explorer

**Public-facing web-first observational workbench · original scientific UI · Windows-friendly local launch · deployable anywhere via Docker**

**Status:** `v0.5.0` — live-data verified research prototype. SPHEREx images are loaded only from NASA/IPAC IRSA. The initial display has no simulated sky or invented observation dates. The program is an independent educational/citizen-science application, not official NASA software.

**Verified live against the real archive (Barnard's Star, QR3):** 130 observation records across a 37-day baseline; registered frames with visible stars; per-pixel local wavelengths; a 40-point exploratory spectrum covering 0.795–4.836 µm from all six detectors (SNR 175–406); and a Gaia DR3 overlay that automatically flags Barnard's Star by its 10.4″/yr proper motion. Screenshots: [Gaia overlay on a real frame](docs/interface-v0.5-gaia-overlay.png), [single registered frame](docs/interface-v0.5-frame-barnard.png).

## Workbench interface · release 0.5.0

- Everything from 0.3 (workbench UI, epoch timeline, A/B controls, honest empty states) retained.
- **Science-correct flag masking** following the official SPHEREx flag-bit table (Explanatory Supplement SSDC-DP-017 v2.0): only fatal bits invalidate pixels; SOURCE-flagged pixels (the stars!) stay visible. Display mode keeps saturated cores visible; photometry uses strict masking.
- **Per-pixel local wavelength** at the target via the file's spectral WCS (A-alternate WCS + WCS-WAVE lookup), with a local λ-match verdict for every A/B pair — the linear variable filter means same-detector frames can sample different wavelengths.
- **On-the-fly exploratory spectrophotometry**: aperture extraction across up to 40 archive exposures in parallel, each point's wavelength from its own exposure's spectral WCS, statistical errors from the VARIANCE extension, interactive per-detector plot and CSV export. Bright-source saturation is handled with a clearly flagged display-mask fallback.
- **Gaia DR3 reference overlay** (IRSA TAP) with proper-motion propagation to the observation epoch, motion arrows, and magnitude-sized markers drawn on the science frames.
- **Target-centred frame selection**: SPHEREx frames span ~3.5°, so archive "intersections" often clip the field; records now carry their off-axis angle and the widest-baseline picker prefers frames where the target sits inside the detector.
- **Vendored Aladin Lite v3 atlas** (no CDN dependency) with multiple sky surveys, retry, and honest tile-server status.
- Bounded retries on all IRSA calls; cutout sizing compensates the service's non-square spectral-image geometry.

## What is implemented

- Original, instrument-style, responsive dark astronomy workbench (not cloned from another project's UI).
- Decimal-degree RA/Dec search and 1–18 arcminute field selection.
- Five challenge targets: Barnard's Star, ε Indi B, WISE 0855−0714, RW Aurigae and R Draconis.
- First-order proper-motion **approximation** for selected named targets, explicitly labelled as excluding parallax (and radial/orbital effects).
- Live IRSA SIA v2 metadata retrieval for SPHEREx QR3/QR2 wide and deep-field surveys; only IRSA source URLs accepted.
- Selection of A/B exposure observations, including dates, reported wavelength ranges, and off-axis angles.
- Archive coverage summary with earliest/latest dated records, baseline length, and one-click widest target-centred baseline.
- Chronological **two-to-eight-exposure sequence playback** with a *shared* display-intensity stretch, date chips, per-frame local λ, and speed selection.
- Optional UTC start/end filters backed by the SIA `TIME` parameter, plus switchable **wide survey / deep field** collections.
- Reproducible selected-observation URLs and downloadable JSON evidence manifests (now including extracted spectra) with release DOI and processing warnings.
- Official SPHEREx FITS cutout downloads via the documented `center` / `size` parameters.
- Local FITS reading (IMAGE/FLAGS/VARIANCE/ZODI/WCS-WAVE), bit-aware flag masking, celestial-WCS reprojection to a common TAN sky grid and **shared A/B brightness stretch**.
- Blink, split, two-frame mean and **exploratory** B−A residual modes; speed selection and reversible controls.
- Transparent percentile-thresholded residual-region review cues, reported in display pixels only and explicitly not detections or significance estimates.
- Reference survey atlas (vendored Aladin Lite v3), clearly separated from SPHEREx frames.
- IRSA source provenance, release, timestamps, wavelength ranges, flag summaries, downloadable display PNG and coordinate-parameter URL sharing.
- API endpoint validation, trusted host/path checks, bounded response sizes, and 29 offline unit tests.

**Scientific caution:** local wavelengths come from the visualization-grade WCS-WAVE lookup, not survey-grade spectral WCS files. Matching local wavelengths does **not** give calibrated difference photometry. WCS registration is interpolated, not flux-preserving. The tool does **not** perform PSF matching or absolute calibration, and must **not** be used to claim a new astronomical discovery.

## How to use — the complete walkthrough

**Quick tour (2 minutes):** open the app → keep **Barnard's Star · motion** selected → press **Find observations** → press **Use widest baseline** → wait for the registered frames to appear → press **▶** to blink two epochs of real SPHEREx sky. Then explore:

| You want to… | Do this |
|---|---|
| Compare two dates | Click **A** then **B** on any rows in *Observation stack* (or click timeline markers) — frames render automatically; the epoch rail shows your baseline |
| See motion / change | Pick **Blink** (alternate), **Split** (side-by-side), **B − A** (signed residual, amber = B brighter), or **Mean** |
| Watch a time series | Press **＋** on 2–8 rows, then choose **Sequence** — chronological playback with one shared brightness scale |
| Get a spectrum | Scroll to *On-the-fly spectrophotometry* → **Extract spectrum** → hover points for details → **↓ CSV** to export |
| Identify fast movers | Render any frame → **✦ Gaia overlay** — cyan rings = Gaia stars at the observation epoch; **amber ring + arrow + "10.4″/yr"** = a fast mover (that's Barnard's Star, found automatically) |
| Inspect details | Hover the frame: the *Data inspector* shows UTC, detector, wavelength range, **local λ at the target**, flagged-pixel fraction; the checklist flags any λ mismatch between your two epochs |
| Zoom into the sky | **＋ / − / ⤢** buttons (right edge), **scroll wheel**, and **drag to pan** — the Gaia overlay scales with the image |
| Put your field in context | *Reference sky atlas* tab — AllWISE W1 mid-infrared imagery loads by default (always available); the sharp field cutout sits on top of a ~1.25° context layer, so zooming out shows real sky. CDS HiPS optical surveys are one click away when the network allows |
| Share / reproduce | **Share view** copies a URL that re-creates the exact view; **↓ Evidence JSON** exports observation IDs, spectra, caveats, and the dataset DOI |
| Keyboard | **Space** = blink play/pause · **Esc** = stop · **?** = help |

**Reading the science honestly:** the λ numbers come from each exposure's own spectral WCS (visualization-grade); a green ✓ on *local wavelength match* means your two epochs sampled the same band at the target. Residual cues in B − A are percentile-thresholded review aids — **not** detections. The tool never fabricates an image, an epoch, or a spectrum.

## Documents in this repository

- **[Project pitch](docs/SPHEREx_Motion_Explorer_Pitch.pdf)** — the full story: challenge, solution, verified evidence, impact, roadmap
- **[Technical documentation](docs/SPHEREx_Motion_Explorer_Tech_Stack.pdf)** — architecture, module reference, science core, API, security, deployment
- [UI design guide](docs/UI_DESIGN_GUIDE.md) · [Competition readiness](docs/COMPETITION_READINESS.md) · [Development roadmap](docs/ROADMAP.md)

## Install and run on Windows

1. Install [Python 3.11 or 3.12](https://www.python.org/downloads/windows/) with **Add Python to PATH** selected.
2. Unzip the project folder, connect to the internet and double-click **`run_windows.bat`**. The first run creates `.venv` (preferring Python 3.12, with 3.11 fallback) and installs Python dependencies.
3. Open **http://127.0.0.1:8000** in your browser (the batch launcher opens it automatically). Keep the terminal window open while using the app.
4. Select a target and field of view, choose QR3/QR2 and **Wide** or **Deep** survey, optionally set UTC date bounds, then click **Find observations**. Pick A/B frames (or **Use widest baseline**), toggle **✦ Gaia overlay**, choose Blink / Split / B−A / Mean / Sequence, and press **Extract spectrum** for the on-the-fly spectrophotometry plot. Use **Export evidence manifest** to save observation IDs, spectra, and processing caveats.

For Linux/macOS: `bash run_unix.sh`, then open the same URL. For manual launch:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

**Docker deployment** (any cloud host or Hugging Face Spaces):

```bash
docker build -t spherex-motion-explorer .
docker run -p 7860:7860 spherex-motion-explorer
```

To run tests: `python -m pytest -q` (29 tests). Tests use synthetic **numerical fixtures strictly in unit tests**—never as visible SPHEREx images.

## Live data caveats and how to troubleshoot

- Requires live access to IRSA; sky-atlas tiles additionally come from CDS HiPS servers. On networks that filter these hosts, archive queries and atlas tiles can fail — the app retries (SIA ×3, cutouts ×3, TAP ×2) and reports honestly instead of showing placeholder content.
- QR3 `spherex_qr3`, QR2 `spherex_qr2`, and their `_deep` variants are confirmed in the September 2026 Caltech/IPAC SPHEREx data-access guide and verified live end-to-end (query → cutout → render → spectrum → catalogue) against real QR3 data for Barnard's Star.
- An empty result may mean missing coverage, an archive release mismatch, a query limit, a target coordinate epoch mismatch, or an off-detector frame. No-image state is intentionally explicit. Under no condition will the code substitute invented observations.
- The UI limits a query to the first 600 SIA records and samples a maximum of 96 rows for responsiveness. Narrow the UTC date interval to reduce sampling bias. Full result pagination remains unfinished.
- Larger than 18′ fields and downloaded cutouts over 28 MB are deliberately blocked in this preview.
- Flag masking follows the official bit table; saturated cores stay visible in display modes (photometric extraction uses strict masking with a flagged fallback for bright sources).
- Sequence mode allows mixed detectors but explicitly marks them as unsuitable for quantitative brightness comparison.

## Architecture

```text
Browser on Windows, Linux, macOS, and mobile
  │
  ├── Original workbench UI (HTML/CSS/JavaScript)
  ├── Vendored Aladin Lite v3 atlas (third-party, no CDN)
  │
  ▼
FastAPI same-origin server
  │
  ├── /api/observations  → IRSA SIA v2 → trusted FITS metadata URLs / UTC filters / off-axis
  ├── /api/render        → IRSA cutout → bit-aware FLAGS → VARIANCE/ZODI → spectral WCS λ
  │                        → celestial WCS reprojection → shared stretch / difference → PNG
  ├── /api/sequence      → 2–8 frames, common WCS + shared brightness scale
  ├── /api/spectrum      → parallel cutout sweep → aperture photometry + local λ per point
  ├── /api/catalog       → IRSA TAP Gaia DR3, proper-motion propagated
  ▼
No local database; bounded in-process FITS/frame caches.
```

## API

```text
GET /api/health
GET /api/observations?ra=269.446&dec=4.771&fov=9&release=qr3&survey=wide&start_date=2025-05-01&end_date=2026-10-30
GET /api/render?ra=...&dec=...&fov=...&a=<source_token>&b=<source_token>&mode=a|b|mean|difference
POST /api/sequence  JSON {"ra": 269.446, "dec": 4.771, "fov": 9, "tokens": ["<token1>","<token2>"]}
GET /api/spectrum?ra=...&dec=...&fov=4&release=qr3&survey=wide&max_files=40
GET /api/catalog?ra=...&dec=...&fov=9&mag_limit=17.5
GET /
```

`/api/render` accepts base64url-encoded **official IRSA on-prem FITS URLs only**, with strict host and path checks. There is no arbitrary URL fetcher. Image response headers include base64url JSON scientific provenance metadata. The API specification is accessible at `/docs`. The sequence API returns PNG frame data and a shared stretch plus source metadata. Rendered PNGs and manifests are **visual/observational research aids**, not certified difference photometry or new-object reports.

## What is still needed for a competitive, publishable Space Apps submission

See [development roadmap](docs/ROADMAP.md), [release validation notes](docs/RELEASE_NOTES.md), and [judging demonstration guidance](docs/DEMO_SCRIPT.md) for engineering stages and [UI and data ethics](docs/UI-AND-DATA-ETHICS.md) for the binding originality and science-integrity standards. In priority order: verify real QR3 queries, verify FITS WCS and pixel flags from live examples, wavelength matching and photometric consistency, PSF matching and uncertainty maps, proper-motion/parallax-aware target location, time/date pagination, six detector coadds, 102-channel cubes, spectrum tool, Gaia/WISE overlay crossmatches, candidate workflow, quantitative detection validation, provenance export and production deployment. Only then package a Tauri-based Windows app using the same web frontend.

## Primary documentation

- [NASA/IPAC IRSA SPHEREx mission archive](https://irsa.ipac.caltech.edu/Missions/spherex.html)
- [IRSA SIA v2 search interface](https://irsa.ipac.caltech.edu/ibe/sia.html)
- [Caltech/IPAC SPHEREx Data Access guide (September 2026)](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/)
- [SPHEREx QR3 dataset DOI](https://doi.org/10.26131/IRSA662)
- [SPHEREx cutout service](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/cutout_tool.html)
- [IRSA SPHEREx Explanatory Supplement](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp_QR.pdf)
- [SPHEREx Data Explorer](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/overview.html)
- [Aladin Lite v3 documentation](https://aladin.cds.unistra.fr/AladinLite/doc/)
- [Astropy WCS documentation](https://docs.astropy.org/en/stable/wcs/)
- [Reproject documentation](https://reproject.readthedocs.io/en/stable/)
- [SIMBAD astronomical object database](https://simbad.cds.unistra.fr/simbad/)

## Credits and licensing

See `LICENSE` and `THIRD_PARTY.md`. NASA/SPHEREx/IRSA data and mission names remain credited to their respective owners; no NASA insignia or project logo is replicated. Aladin Lite is embedded as an astronomy component with its native attribution intact. This independently developed UI is a workbench design, not an attempt to pass itself off as an official NASA/ESA/CDS site.
