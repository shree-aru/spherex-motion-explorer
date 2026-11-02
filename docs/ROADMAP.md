# Engineering and judging roadmap

## P0 — Genuine data proof (first milestone)

- [x] Confirm QR3/QR2 and `_deep` collection identifiers in published September 2026 Caltech/IPAC documentation.
- [ ] Run live SIA discovery on representative targets, including record completeness and `MAXREC=0` validation.
- [ ] Download sample QR2/QR3 cutouts at a safe fixed RA/Dec, inspect all HDUs, WCS keywords, flags, BUNIT and PSF extension.
- [ ] Test first real rendered frame in all five challenge targets; document *actual* observations and lack of coverage where relevant.
- [ ] Write integration regression fixtures using a small legally redistributed IRSA FITS cutout, including origin, checksum, and citation.
- [ ] Compare the reprojected WCS against direct Astropy world-to-pixel checks with measured pixel error.
- [ ] Verify that same target is covered in at least two observations with comparable wavelength and adequate baseline.

## P1 — High-trust competition core

- [x] Basic optional UTC `TIME` range filter and wide/deep choice.
- [x] Archive coverage summary with earliest/latest dated records and returned baseline.
- [x] One-click widest same-detector baseline selection for the primary judge workflow.
- [ ] Paginated, season-aware SIA discovery with complete results (currently capped at first 600 records).
- [ ] Per-pixel wavelength WCS retrieval; pair observations by matched physical wavelength.
- [ ] PSF/kernel matching, exposure calibration verification, background matching and propagated variance after reprojection.
- [ ] Robust registration QA, flux-conservation validation and explicit masks.
- [x] Prototype 2–8-frame chronologically ordered blink using shared brightness stretch and WCS registration (offline-tested).
- [ ] Full cadence/coverage-aware series, calibrated difference/weighted coadds and quantitative time track.
- [ ] First-order position prediction with catalogue epoch, proper motions, annual parallax and uncertainties; flag approximate orbital trajectories.
- [x] Preliminary JSON evidence export includes identifiers, times, dataset DOI, warnings and view URL.
- [x] Transparent percentile-thresholded residual-region cues for human review; no discovery or significance claim.
- [ ] Audit-ready export with FITS SHA-256, local wavelength, registration residuals, calibration and variance.
- [ ] Acceptance tests: centroid recovery on planted sources, null residual rate on static stars, astrometric RMS and noise estimates, no false 'discovery' classification.

## P2 — SPHEREx differentiators

- [ ] 102-channel cube/wavelength scrubber backed by the appropriate SPHEREx mosaic tool or scientifically correct cube assembly.
- [ ] Detector-specific coadds with variance-weighted coverage and calibration checks.
- [ ] Quick *exploratory* spectrum and separate official IRSA spectrophotometry integration; uncertainty plots.
- [ ] Gaia / WISE catalogue overlays with documented coordinate epochs and search-radius uncertainty.
- [ ] Apparent-motion trail and candidate quality diagnostics; compare neighboring spectral bands to reject artifacts.
- [ ] Optional known solar-system object path through IRSA MOST; do not mistake a moving source for a new planet.

## P3 — Public release + Windows edition

- [ ] HTTPS cloud deployment of same web app; privacy review, retention limits, safe caching, API rate limits and abuse controls.
- [ ] Accessibility audit (keyboard, contrast, reduced motion, screen readers).
- [ ] Tune large-result pages, FITS cutout prefetching and redis/worker architecture based on measured latency.
- [ ] Windows installer via Tauri 2 using the existing frontend; local FITS open and optional offline cache.
- [ ] User study and scientific reproducibility acceptance review.

## Demonstration order for judges

**Barnard's Star** — two actual SPHEREx epochs → registered blink → signed residual → proper motion caveat.

**WISE 0855−0714** — historical coordinate vs epoch-corrected sky location → proper-motion/parallax caveats.

**ε Indi B** — multi-component brown dwarf and larger field; do not confuse ε Indi A and B.

**RW Aur and R Dra** — temporal flux variation vs positional motion (after wavelength and photometric matching exists).

**End:** reproducible link and data provenance; do not claim a discovery without scientifically validated follow-up.
