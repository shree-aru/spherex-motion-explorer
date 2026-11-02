# SPHEREx Motion Explorer — release 0.3.0

## Competition hardening pass

- Added archive coverage metadata: dated-record count, earliest/latest UTC epochs, and returned baseline.
- Added a one-click widest same-detector baseline selector to make the primary time-domain workflow explicit.
- Added auditable residual-region review cues based on a documented percentile threshold. These are display-pixel human-review aids, not detections or significance estimates.
- Added a visible three-step workflow and archive coverage card for first-time public users.
- Expanded the offline suite to 21 tests.

## New original scientific workbench

- Desktop-optimized, restrained navy/charcoal multi-pane layout. Original hand-authored HTML/CSS and JavaScript; no copied layout or third-party dashboard template.
- Functional left navigation rail and contextual astronomy help dialog.
- Real archive-only epoch timeline with interactive selection and UTC extent labels.
- Upgraded sky-viewer information, real-source boundaries, and A/B animation controls.
- Actual wavelength-range display and UTC baseline, always sourced from observation metadata.
- Frame stack relocated adjacent to scientific inspector for faster workflow.
- No synthetic sky images, random star overlays, or fabricated measurements introduced.
- End-to-end browser view tested with Chromium using in-memory page content. Verified help, navigation, source selection and mobile overflow.
- Offline suite: 20 passing tests.

**Validation limit:** no actual SPHEREx FITS file was retrieved in this workspace; calibration and live network integrations still require real-data checks. The interface remains a research preview, not validated discovery software.

---

# Preview v0.2 — Validation and known limitations

**Date:** October 30, 2026. **Claimed status:** offline-tested development preview, not validated against NASA's live archives.

## Implemented in this iteration

- 2–8 frame chronological sequence with one common display intensity scale, selectable frame chips, speed control, and per-frame UTC label.
- Optional UTC date-range search through SIA `TIME`; wide and deep field selectors for QR2 and QR3.
- Evidence manifest export with selected observation metadata, release DOI, processing caveats and reproducible view parameters.
- Browser-side selected exposure restoration when opening a shared view URL.
- Updated original data-first UI without copied NASA/ESA interface graphics or fabricated sky fields.

## Verification performed

| Check | Result | Scope |
|---|---|---|
| Python API and numerical tests | 17 passed | Synthetic test matrices only, no NASA server contact |
| JavaScript parser (`node --check`) | Passed | Syntax |
| Browser interactions (headless Chromium) | Passed | Mocked archive responses: selection, sequence, play/pause, evidence export, no uncaught script error |
| UI screenshot inspection | Passed | Desktop empty-data view; no invented astronomy imagery |
| QR3 and `_deep` collection identifiers | Verified | [Caltech/IPAC SPHEREx data access](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/) |
| Actual SIA results for five challenge targets | **Not verified** | Container lacks outbound NASA archive access |
| Real SPHEREx FITS, cutouts and WCS | **Not verified** | Astropy and reproject could not be installed in this container |
| Motion/photometry accuracy against trusted calibration | **Not verified** | No PSF-matching or local spectral WCS validation yet |
| Windows launcher / cloud deployment | **Not verified** | Script provided; needs testing on real Windows 11 workstation |

## Specific scientific constraints

A sequence is **not** a time-dependent flux measurement. All frames are aligned using interpolated WCS coordinates and presented using a common intensity scale, which reduces but does not remove misleading brightness effects. Images can differ in wavelength at the selected sky location, PSF, calibration, spacecraft background and mask coverage. Mixed detector ranges are explicitly highlighted. A significant residual is **not** proof of a new object. 

The first 600 SIA records may not contain the best epochs; UTC filters help but paginated/full-coverage queries are still needed. IRSA's weekly data ingestion can appear in directories and the GUI before SIA indexes catch up.

## Next science-critical milestone

Using a Windows Python 3.12 environment with outbound access, query live QR3 and QR2 for Barnard's Star and one variable-star field. Download one verified SPHEREx cutout and inspect all science/flags/variance/wavelength-WCS extensions, compare WCS positions, compute per-frame coverage, and only then assess motions and residuals. Record input observation IDs, FITS hashes and date-separated values in a reproducibility notebook.
