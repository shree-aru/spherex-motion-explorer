"""SPHEREx Motion Explorer - project pitch PDF (body). Cover merged separately."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                KeepTogether, HRFlowable, CondPageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ── Fonts (Windows host paths) ──
FONT_DIR = r'C:\Windows\Fonts'
pdfmetrics.registerFont(TTFont('Times New Roman', os.path.join(FONT_DIR, 'times.ttf')))
pdfmetrics.registerFont(TTFont('Times New Roman Bold', os.path.join(FONT_DIR, 'timesbd.ttf')))
pdfmetrics.registerFont(TTFont('Calibri', os.path.join(FONT_DIR, 'calibri.ttf')))
pdfmetrics.registerFont(TTFont('Calibri Bold', os.path.join(FONT_DIR, 'calibrib.ttf')))
registerFontFamily('Times New Roman', normal='Times New Roman', bold='Times New Roman Bold',
                   italic='Times New Roman', boldItalic='Times New Roman Bold')
registerFontFamily('Calibri', normal='Calibri', bold='Calibri Bold')

# ━━ Color Palette (pdf.py palette.cascade, seed 42) ━━
PAGE_BG = colors.HexColor('#f4f5f5')
SECTION_BG = colors.HexColor('#f0f1f2')
CARD_BG = colors.HexColor('#e8eaeb')
HEADER_FILL = colors.HexColor('#32454e')
COVER_BLOCK = colors.HexColor('#566a74')
BORDER = colors.HexColor('#acbdc5')
ICON = colors.HexColor('#4b86a4')
ACCENT = colors.HexColor('#c2475b')
TEXT_PRIMARY = colors.HexColor('#131515')
TEXT_MUTED = colors.HexColor('#747b7e')

H1 = ParagraphStyle('H1', fontName='Times New Roman', fontSize=20, leading=26,
                    textColor=HEADER_FILL, spaceBefore=18, spaceAfter=8)
H2 = ParagraphStyle('H2', fontName='Times New Roman', fontSize=14, leading=19,
                    textColor=HEADER_FILL, spaceBefore=14, spaceAfter=6)
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
STAT = ParagraphStyle('STAT', fontName='Times New Roman', fontSize=19, leading=23,
                      textColor=ACCENT, alignment=TA_CENTER)
STATL = ParagraphStyle('STATL', fontName='Calibri', fontSize=8.5, leading=11,
                       textColor=TEXT_MUTED, alignment=TA_CENTER)

AVAIL = A4[0] - 2 * 2 * cm


def callout_row(stats):
    """Row of metric callout boxes: [(value, label), ...]"""
    n = len(stats)
    w = (AVAIL - (n - 1) * 8) / n
    cells = []
    for value, label in stats:
        inner = Table([[Paragraph('<b>%s</b>' % value, STAT)], [Paragraph(label, STATL)]],
                      colWidths=[w - 4])
        inner.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
            ('BOX', (0, 0), (-1, -1), 0.8, ICON),
            ('TOPPADDING', (0, 0), (-1, 0), 8), ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        cells.append(inner)
    row = Table([cells], colWidths=[w] * n, hAlign='CENTER')
    row.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                             ('LEFTPADDING', (0, 0), (-1, -1), 0),
                             ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    return KeepTogether([Spacer(1, 6), row, Spacer(1, 10)])


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
story.append(Paragraph('<b>SPHEREx Motion Explorer</b>', ParagraphStyle(
    'T', fontName='Times New Roman', fontSize=15, leading=20, textColor=HEADER_FILL)))
story.append(Paragraph('Project pitch - NASA Space Apps Challenge 2026 - v0.5.0, November 2026', MUTED))
story.append(HRFlowable(width='100%', thickness=1.1, color=ICON, spaceAfter=10))

story.extend(h('1. The Challenge'))
story.append(Paragraph(
    'Since May 2025, NASA’s SPHEREx mission has mapped the entire sky every six months in 102 '
    'bands of near-infrared light, returning images of more than a billion objects. Comets, asteroids, '
    'brown dwarfs and planets reveal themselves by <b>shifting position between images</b> - the same '
    'technique that discovered Pluto in 1930. No single person can sift through that volume of data. '
    'The Space Apps challenge asked for a public-facing web tool that displays SPHEREx images of any '
    'patch of sky and makes temporal changes easy for anyone to see.', BODY))
story.append(callout_row([('102', 'infrared bands per sky map'),
                          ('1B+', 'objects in the SPHEREx archive'),
                          ('6 mo', 'all-sky mapping cadence'),
                          ('0', 'images simulated or faked')]))

story.extend(h('2. Our Answer'))
story.append(Paragraph(
    'SPHEREx Motion Explorer is an observational workbench that turns the official NASA/IPAC IRSA '
    'archive into an interactive time-domain experience. Enter any sky coordinate, retrieve every '
    'compatible real SPHEREx exposure, and compare epochs as registered, blink-comparable frames. '
    'The tool adds the scientific glue the raw archive lacks: per-pixel wavelength awareness, '
    'bit-correct quality masking, on-the-fly spectrophotometry, and a Gaia proper-motion overlay '
    'that flags fast movers automatically.', BODY))
story.append(callout_row([('130', 'real QR3 records retrieved for Barnard’s Star'),
                          ('37 d', 'verified temporal baseline'),
                          ('40/40', 'spectrum points extracted, 0 failures'),
                          ('10.4"/yr', 'proper motion auto-detected by the overlay')]))

story.extend(h('3. The Judging Journey - Six Steps'))
steps = [
    ('01', 'Choose a field', 'Five preset challenge targets (Barnard’s Star, epsilon Indi B, WISE 0855-0714, RW Aurigae, R Draconis) or any RA/Dec. Field of view 1-18 arcmin, QR2/QR3, wide or deep collections, UTC filters.'),
    ('02', 'Retrieve real observations', 'The app queries IRSA SIA v2 live. 130 dated records returned for Barnard’s Star; every record shows its detector, wavelength range, and off-axis angle so users pick frames that truly contain the target.'),
    ('03', 'Compare epochs', 'One click selects the widest target-centred baseline. Blink, split, mean, and exploratory B-minus-A modes share one display stretch so brightness changes are not masked by per-frame contrast.'),
    ('04', 'See the physics', 'Each frame reports its LOCAL wavelength at the target from the spectral WCS - the tool exposed a 0.50 micron mismatch inside one detector band, and a 0.23 micron difference between two epochs of the same band.'),
    ('05', 'Extract a spectrum', 'The on-the-fly extractor sweeps up to 40 archive files in parallel and builds a 0.8-4.8 micron spectrum with per-point statistical errors, detector colour-coding, and CSV export.'),
    ('06', 'Overlay the sky', 'Gaia DR3 stars (epoch-propagated) ring every field star; any source moving faster than 1 arcsec/yr gets an amber ring, a motion arrow, and a measured speed label. A two-layer AllWISE atlas puts the field in mid-infrared context.'),
]
rows = [[n, t, d] for n, t, d in steps]
story.append(styled_table(['Step', 'Action', 'What actually happens (verified live)'], rows,
                          [0.07, 0.18, 0.75]))

story.extend(h('4. Built for Trust: Science Integrity by Design'))
story.append(Paragraph(
    'Most astronomy demo tools break quietly on real data. Ours publishes its own audit trail. The '
    'flag-masking system follows the official SPHEREx Explanatory Supplement bit table - critically, '
    'bit 21 (SOURCE) marks pixels containing real star flux and is never masked, while genuinely '
    'fatal statuses (saturation, non-linearity, persistence, satellite streaks) are. A naive mask '
    'deleted 96 percent of pixels and rendered Barnard’s Star invisible; ours restores 95 percent '
    'valid coverage. Every rendered frame carries a provenance header, every spectrum point is '
    'labelled statistical-only, and every screen states what the tool is not: it does not certify '
    'discoveries.', BODY))
story.append(styled_table(
    ['Deliberate honesty feature', 'Why it matters'],
    [['Honest empty states', 'No coverage means an explicit message - invented sky data can never appear'],
     ['Local wavelength matching', 'Same detector does not mean same band; the tool quantifies the mismatch'],
     ['Saturation-aware spectra', 'Bright-source points are flagged as lower limits, never silently wrong'],
     ['Evidence manifests', 'One JSON export preserves observation IDs, caveats, DOI, and a reproducible URL'],
     ['Residual cues, not detections', 'Difference-mode highlights are review aids, explicitly not claims']],
    [0.34, 0.66]))

story.extend(h('5. Architecture at a Glance'))
story.append(Paragraph(
    'A dependency-light stack chosen so any volunteer can run it: vanilla HTML/CSS/JavaScript '
    'frontend (no build step), a FastAPI backend that brokers every archive call, Astropy + reproject '
    'for FITS science, Aladin Lite v3 vendored locally (no CDN dependency), and Docker packaging. '
    'Everything talks to the official NASA/IPAC IRSA services - SIA v2 for discovery, IBE for '
    'cutouts and AllWISE reference imagery, TAP for Gaia.', BODY))
story.append(styled_table(
    ['Layer', 'Technology', 'Role'],
    [['Frontend', 'Vanilla JS + Aladin Lite v3 (vendored)', 'Workbench UI, WCS canvas overlays, zoom/pan, spectrum plot'],
     ['Backend', 'Python FastAPI + httpx', 'Archive brokering, retries, SSRF allowlist, bounded caches'],
     ['Science', 'Astropy WCS + reproject + numpy', 'Flag masking, reprojection, aperture photometry, mini-FITS generation'],
     ['Data', 'NASA/IPAC IRSA (SIA, IBE, TAP)', 'Exposure discovery, FITS cutouts, AllWISE atlas, Gaia DR3'],
     ['Delivery', 'Docker + Cloudflare tunnel / any host', 'Public URL without infrastructure cost']],
    [0.14, 0.36, 0.50]))

story.extend(h('6. Verified, Not Claimed'))
story.append(Paragraph(
    'Every number in this document was measured against the live archive on the submission day. The '
    'pipeline runs end-to-end on all five challenge targets; Barnard’s Star and epsilon Indi B were '
    'exercised most deeply.', BODY))
story.append(callout_row([('95%', 'valid pixels restored by bit-correct masking'),
                          ('0.8-4.8 um', 'verified spectrum coverage, all 6 detectors'),
                          ('SNR 175-406', 'per-point signal-to-noise on Barnard’s Star'),
                          ('300', 'Gaia reference stars overlaid per field')]))

story.extend(h('7. Who It Serves'))
for line in [
    '<b>Citizen scientists</b> - a zero-install browser workbench that mirrors professional blink-comparison workflows, with honest guidance at every step.',
    '<b>Educators and students</b> - real mission data with the physics (variable filter, saturation, proper motion) made visible instead of hidden.',
    '<b>Researchers</b> - a fast triage layer over IRSA: wavelength-matched epoch selection, quick spectra, and evidence exports reproducible from archive IDs.',
]:
    story.append(Paragraph('• ' + line, BULLET))

story.extend(h('8. Roadmap'))
story.append(styled_table(
    ['Horizon', 'Item'],
    [['Next', 'Season-aware SIA pagination beyond 600 records; PSF-matched difference photometry using the EPSF extension'],
     ['Next', 'Official IRSA spectrophotometry cross-checks and uncertainty plots beside our exploratory spectrum'],
     ['Later', 'Solar-system object path overlays (MOST) so known asteroids are never mistaken for discoveries'],
     ['Later', 'Multi-tile AllWISE mosaics beyond the 1.25-degree context limit; hosted always-on deployment']],
    [0.16, 0.84]))

story.extend(h('9. Try It'))
for line in [
    '<b>Public URL:</b> live demo tunnel (printed by start_public.bat on the project machine)',
    '<b>Source code:</b> github.com/shree-aru/spherex-motion-explorer',
    '<b>Local run:</b> double-click run_windows.bat, open http://127.0.0.1:8000',
    '<b>Data credit:</b> SPHEREx data are served live from NASA/IPAC IRSA; the tool is an independent citizen-science application, not official NASA software.',
]:
    story.append(Paragraph('• ' + line, BULLET))
story.append(Spacer(1, 8))
story.append(Paragraph(
    'Built with enthusiasm by a team that believes the sky belongs to everyone - and that honest '
    'tools make better discoveries.', MUTED))

doc = SimpleDocTemplate(os.path.join(os.path.dirname(__file__), '_pitch_body.pdf'),
                        pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                        title='SPHEREx Motion Explorer - Project Pitch',
                        author='Z.ai', creator='Z.ai',
                        subject='NASA Space Apps Challenge 2026 project pitch')


def footer(canvas, doc_):
    canvas.saveState()
    canvas.setFont('Times New Roman', 7.5)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(2 * cm, 1.1 * cm, 'SPHEREx Motion Explorer - project pitch')
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, 'Page %d' % doc_.page)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.35 * cm, A4[0] - 2 * cm, 1.35 * cm)
    canvas.restoreState()


doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('pitch body built')
