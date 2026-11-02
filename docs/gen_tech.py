"""SPHEREx Motion Explorer - technical documentation PDF (body). Cover merged separately."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, CondPageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

FONT_DIR = r'C:\Windows\Fonts'
pdfmetrics.registerFont(TTFont('Times New Roman', os.path.join(FONT_DIR, 'times.ttf')))
pdfmetrics.registerFont(TTFont('Times New Roman Bold', os.path.join(FONT_DIR, 'timesbd.ttf')))
pdfmetrics.registerFont(TTFont('Calibri', os.path.join(FONT_DIR, 'calibri.ttf')))
registerFontFamily('Times New Roman', normal='Times New Roman', bold='Times New Roman Bold',
                   italic='Times New Roman', boldItalic='Times New Roman Bold')

PAGE_BG = colors.HexColor('#f4f5f5')
CARD_BG = colors.HexColor('#e8eaeb')
HEADER_FILL = colors.HexColor('#32454e')
BORDER = colors.HexColor('#acbdc5')
ICON = colors.HexColor('#4b86a4')
ACCENT = colors.HexColor('#c2475b')
TEXT_PRIMARY = colors.HexColor('#131515')
TEXT_MUTED = colors.HexColor('#747b7e')

H1 = ParagraphStyle('H1', fontName='Times New Roman', fontSize=20, leading=26,
                    textColor=HEADER_FILL, spaceBefore=18, spaceAfter=8)
BODY = ParagraphStyle('BODY', fontName='Times New Roman', fontSize=10.5, leading=16,
                      textColor=TEXT_PRIMARY, alignment=TA_JUSTIFY, spaceAfter=8)
BULLET = ParagraphStyle('BULLET', fontName='Times New Roman', fontSize=10.5, leading=15,
                        textColor=TEXT_PRIMARY, leftIndent=14, spaceAfter=4)
MUTED = ParagraphStyle('MUTED', fontName='Times New Roman', fontSize=9, leading=13,
                       textColor=TEXT_MUTED, spaceAfter=6)
TH = ParagraphStyle('TH', fontName='Times New Roman', fontSize=10, leading=13,
                    textColor=colors.white, alignment=TA_CENTER)
TC = ParagraphStyle('TC', fontName='Times New Roman', fontSize=9.5, leading=13,
                    textColor=TEXT_PRIMARY, alignment=TA_LEFT)
CODE = ParagraphStyle('CODE', fontName='Calibri', fontSize=9, leading=13,
                      textColor=TEXT_PRIMARY, backColor=CARD_BG, borderPadding=5,
                      leftIndent=6, spaceAfter=8)

AVAIL = A4[0] - 4 * cm


def styled_table(head, rows, ratios):
    widths = [r * AVAIL for r in ratios]
    data = [[Paragraph('<b>%s</b>' % h, TH) for h in head]]
    for row in rows:
        data.append([Paragraph(c, TC) for c in row])
    t = Table(data, colWidths=widths, hAlign='CENTER', repeatRows=1)
    style = [('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL),
             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
             ('GRID', (0, 0), (-1, -1), 0.4, BORDER),
             ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
             ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]
    for i in range(1, len(data)):
        style.append(('BACKGROUND', (0, i), (-1, i), colors.white if i % 2 else CARD_BG))
    t.setStyle(TableStyle(style))
    return t


def h(text):
    return [CondPageBreak(3.2 * cm), Paragraph('<b>%s</b>' % text, H1),
            HRFlowable(width='100%', thickness=1.1, color=ICON, spaceAfter=8)]


story = []
story.append(Paragraph('<b>SPHEREx Motion Explorer - Technical Documentation</b>',
                       ParagraphStyle('T', fontName='Times New Roman', fontSize=15, leading=20,
                                      textColor=HEADER_FILL)))
story.append(Paragraph('v0.5.0 - stack, data flow, science core, and operations - November 2026', MUTED))
story.append(HRFlowable(width='100%', thickness=1.1, color=ICON, spaceAfter=10))

story.extend(h('1. System Architecture'))
story.append(Paragraph(
    'A three-tier, zero-database design: the browser renders everything; a same-origin FastAPI '
    'process brokers all archive traffic (adding retries, allowlists, and bounded caches); NASA/IPAC '
    'IRSA remains the only source of science data. No invented data exists anywhere in the pipeline.', BODY))
story.append(styled_table(
    ['Tier', 'Components', 'Responsibility'],
    [['Browser', 'Vanilla HTML/CSS/JS, Aladin Lite v3 (vendored, 2.4 MB, WebGL2)', 'Workbench UI, epoch timeline, WCS canvas overlays, zoom/pan, SVG spectrum plot'],
     ['API server', 'FastAPI + uvicorn + httpx (Python 3.12)', 'Six endpoints brokering IRSA SIA/IBE/TAP; retries with backoff; SSRF allowlists; bounded LRU caches'],
     ['Science core', 'Astropy 8.0.2 WCS, reproject 0.21, numpy, Pillow', 'Flag-bit masking, TAN reprojection, aperture photometry, spectral-WCS interpolation, mini-FITS generation'],
     ['Archive', 'NASA/IPAC IRSA - SIA v2, IBE (search + cutouts), TAP', 'SPHEREx QR2/QR3 exposure metadata and FITS cutouts; AllWISE coadds; Gaia DR3']],
    [0.13, 0.37, 0.50]))
story.append(Paragraph(
    'Browser → FastAPI (same origin) → IRSA → FITS bytes → Astropy masking + '
    'reprojection → PNG/JSON → browser canvas. Every response carries provenance headers.', BODY))

story.extend(h('2. Backend Modules'))
story.append(styled_table(
    ['Module', 'Lines', 'Responsibility'],
    [['backend/archive.py', '~140', 'SIA v2 CSV parsing (Caltech/IPAC format), per-record wavelength ranges, great-circle off-axis angles, UTC-to-MJD TIME filters, 3-attempt retry'],
     ['backend/flags.py', '~80', 'Official 32-bit flag semantics from the Explanatory Supplement; strict vs display mask levels; per-bit provenance summaries'],
     ['backend/science.py', '~330', 'Cutout fetch (size-padded, cached), fatal-bit masking, VARIANCE/ZODI extraction, local-wavelength interpolation, reprojection to a shared TAN grid, stretch/difference/sequence rendering, wavelength-match verdicts'],
     ['backend/spectrum.py', '~180', 'Parallel aperture spectrophotometry across up to 60 files; adaptive strict-to-display mask fallback for saturated cores; even wavelength sampling preferring target-centred frames'],
     ['backend/catalog.py', '~110', 'IRSA TAP Gaia DR3 queries (table gaia_dr3_source), proper-motion propagation to the observation epoch, VOTABLE error surfacing'],
     ['backend/atlas.py', '~150', 'AllWISE coadd reference imagery: IBE search (POS=ra,dec), tile selection, gzip cutout, asinh display FITS with preserved WCS'],
     ['backend/app.py', '~150', 'FastAPI wiring: /api/health, /observations, /render, /sequence, /spectrum, /catalog, /atlas_image, /net_check; coordinate validation; static frontend mount']],
    [0.20, 0.08, 0.72]))

story.extend(h('3. The Science Core'))
story.extend(h('3.1 Bit-correct flag masking'))
story.append(Paragraph(
    'SPHEREx L2b FLAGS extensions are 32-bit status bitmaps. The naive <i>flags != 0</i> rule masks '
    'bit 21 (SOURCE - pixels containing real star flux, set on ~84 percent of pixels in typical '
    'fields) and produced 0.15 percent valid coverage: blank images. Our mask follows the official '
    'bit table (SSDC-DP-017 v2.0, pages 31-32):', BODY))
story.append(styled_table(
    ['Class', 'Bits', 'Treatment'],
    [['Fatal (strict)', 'TRANSIENT 0, OVERFLOW 1, SUR_ERROR 2, NONFUNC 6, DICHROIC 7, MISSING_DATA 9, HOT 10, COLD 11, PHANMISS 14, NONLINEAR 15, PERSIST 17, OUTLIER 19, CROSSTALK 20, GHOST 22-24, STREAK 25, BLOOM 26, SNOWBALL 27, HALO 28, SATELLITE_HALO 29', 'Masked for display and photometry'],
     ['Display-keep', 'saturated-core family (0/1/2/15/17/19/20/22-29)', 'Kept visible in visual modes so bright stars are not holes; strict level still masks them for photometry'],
     ['Always visible', 'SOURCE 21, FULLSAMPLE 12', 'Flux-bearing and informational - never masked']],
    [0.16, 0.60, 0.24]))
story.extend(h('3.2 Per-pixel local wavelength'))
story.append(Paragraph(
    'SPHEREx uses a linear variable filter: the wavelength sampled at a sky position depends on where '
    'it lands on the detector, so two exposures of the same detector band can sample different '
    'wavelengths. The tool maps the target through the exposure’s celestial WCS to a cutout pixel, '
    'converts via the alternate LINEAR ‘A’ WCS (0-based active-pixel coordinates, CRPIX*A) to the '
    'original detector frame, and bilinearly interpolates the 9x9 WCS-WAVE lookup grid. Verified '
    'result: lambda = 1.728 vs 2.224 um for two D3 frames (a 0.50 um mismatch the file-level metadata '
    'cannot reveal), and 0.776 vs 1.005 um across two D1 epochs.', BODY))
story.extend(h('3.3 Exploratory spectrophotometry'))
story.append(Paragraph(
    'Each AllWISE-style pass extracts r = 2 pixel aperture sums with a 3-6 pixel annulus background '
    'from up to 60 evenly wavelength-sampled files (6 concurrent downloads, 3-attempt retries). '
    'Errors are the quadrature sum of the VARIANCE extension over the aperture. Bright sources '
    'saturate SPHEREx cores; when the strict mask empties the aperture, extraction retries with the '
    'display mask and flags the point saturated_core=true (a labelled lower limit). Verified run: '
    '40/40 points, 0.795-4.836 um, SNR 175-406, all six detectors represented.', BODY))

story.extend(h('4. Frontend Engineering'))
for b in [
    'Zero build step: three static files (index.html, app.js, style.css) served by FastAPI - a volunteer can read every line.',
    'Aladin Lite v3 vendored locally (aladin-lite@3.8.2, ES module with inlined WASM) and published as window.A via a module shim - no CDN dependency, works on filtered networks.',
    'Gaia overlay: epoch-propagated star positions projected through the display grid WCS into per-frame canvases (split-mode aware), with proper-motion arrows exaggerated 50x and a translucent caption strip.',
    'Frame zoom/pan: CSS transforms on wrapper divs containing both the science image and its overlay canvas, so circles, rings, and motion arrows stay locked to their stars at any zoom; wheel, buttons, and pointer-drag pan.',
    'Two-layer reference atlas: a sharp field cutout over a ~1.25-deg AllWISE context image, both generated server-side as WCS-preserved mini-FITS and displayed with Aladin displayFITS.',
    'URL deep links (ra/dec/fov/release/survey/band/a/b/mode/sequence/view) reproduce any view; evidence manifests export observation IDs, spectra, caveats, and the dataset DOI.',
]:
    story.append(Paragraph('• ' + b, BULLET))

story.extend(h('5. API Reference'))
story.append(styled_table(
    ['Endpoint', 'Purpose', 'Key parameters'],
    [['GET /api/health', 'Service + scientific-engine status', '-'],
     ['GET /api/observations', 'IRSA SIA v2 exposure discovery', 'ra, dec, fov, release, survey, start_date, end_date'],
     ['GET /api/render', 'Registered PNG frames + provenance', 'ra, dec, fov, a, b, mode=a|b|mean|difference'],
     ['POST /api/sequence', '2-8 frame chronological playback', 'JSON body: ra, dec, fov, tokens[]'],
     ['GET /api/spectrum', 'On-the-fly spectrophotometry', 'ra, dec, fov, release, survey, max_files (4-60)'],
     ['GET /api/catalog', 'Gaia DR3 overlay, epoch-propagated', 'ra, dec, fov, mag_limit, epoch'],
     ['GET /api/atlas_image', 'AllWISE reference mini-FITS', 'ra, dec, fov, ref=wise, tier=detail|context'],
     ['GET /api/net_check', 'Tile-host reachability probe', 'host (allowlisted CDS hosts)']],
    [0.24, 0.36, 0.40]))

story.extend(h('6. Reliability, Security, Testing'))
for b in [
    '<b>Retries with backoff:</b> SIA x3, cutouts x3, TAP x2, IBE x3 - the IRSA route intermittently stalls on some networks; every layer degrades honestly instead of fabricating content.',
    '<b>SSRF hardening:</b> image sources are base64url tokens validated against an allowlist (https, irsa.ipac.caltech.edu host, /ibe/data/spherex/ path, .fits extension, no query/credentials). Net-check hosts are additionally allowlisted.',
    '<b>Bounded resources:</b> cutouts capped at 28 MB, reference tiles at 60 MB, sequences at 8 frames, spectrum sweeps at 60 files, LRU caches on cutouts (48), frames (24), and atlas products (16).',
    '<b>Testing:</b> 29 offline unit tests cover flag semantics (bit 21 never masked), palette-free rendering, aperture photometry on synthetic frames, spectral-WCS interpolation, file sampling, API validation, and the HTML/JS id contract.',
]:
    story.append(Paragraph('• ' + b, BULLET))

story.extend(h('7. Deployment'))
story.append(Paragraph(
    'The Dockerfile (python:3.12-slim) runs uvicorn on $PORT as an unprivileged user - deployable to '
    'any container host. For zero-cost demonstrations, start_public.bat launches the server plus a '
    'Cloudflare quick tunnel and prints a public HTTPS URL. Requirements: Python 3.11/3.12 or '
    'Docker; outbound access to irsa.ipac.caltech.edu (CDS HiPS optional for the optical surveys).', BODY))
story.append(Paragraph('docker build -t spherex-motion-explorer . → docker run -p 7860:7860 spherex-motion-explorer', CODE))

story.extend(h('8. Known Limitations'))
for b in [
    'WCS-WAVE wavelengths are visualization-grade (the supplement recommends the separate spectral-WCS files for science analysis).',
    'No PSF matching, aperture correction, or absolute calibration; difference modes remain visual triage aids.',
    'SIA discovery caps at 600 records per query (pagination on the roadmap).',
    'Reference-atlas context is bounded by the AllWISE coadd tile (~1.25 deg); full-sky zoom-out requires CDS HiPS reachability.',
]:
    story.append(Paragraph('• ' + b, BULLET))

doc = SimpleDocTemplate(os.path.join(os.path.dirname(__file__), '_tech_body.pdf'),
                        pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                        title='SPHEREx Motion Explorer - Technical Documentation',
                        author='Z.ai', creator='Z.ai',
                        subject='Technology stack and data-flow documentation')


def footer(canvas, doc_):
    canvas.saveState()
    canvas.setFont('Times New Roman', 7.5)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(2 * cm, 1.1 * cm, 'SPHEREx Motion Explorer - technical documentation')
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, 'Page %d' % doc_.page)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.35 * cm, A4[0] - 2 * cm, 1.35 * cm)
    canvas.restoreState()


doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('tech body built')
