# SPHEREx Motion Explorer — original interface specification (v0.3)

## Design objectives

Build a credible observatory data workbench, rather than a decorative "AI space dashboard." Use established astronomy conventions (RA/Dec, UTC, wavelength, WCS, detector selection, calibrated data provenance) without cloning a specific application. Keep the interaction hierarchy consistent with professional Windows instruments.

## Visual architecture

1. **Top mission bar** — independent application name, archive attribution, shareable view action, help.
2. **Narrow navigation rail** — meaningful destinations and actions (Explore, Frames, Compare, Atlas, Metadata); none is just a decorative mock control.
3. **Observation timeline** — chronological archival timestamps, selection highlighted by role, no fictional timeline ticks or dates.
4. **Target acquisition pane** — reference targets; decimal RA and Dec; field of view; release, detector, survey and UTC filters. Input remains compact enough for a 1080p research workstation.
5. **Sky viewport** — intentionally blank until a real SPHEREx image is returned, with separate external reference atlas. WCS display controls and epoch labels are visible next to the actual image.
6. **Time analysis controls** — A/B pairing, blink, split, B−A exploratory residual, mean, 2–8-image chronological sequence, playback rate, reproducible export.
7. **Exposure and inspector pane** — real archive records plus date/wavelength/flag metadata and explicit processing limitations.
8. **Metadata-driven science panels** — wavelength *coverage* and time-baseline status, never a synthesized spectrum, light curve, fake SNR or fake candidate.

## Design system

- Deep navy background and slightly raised slate panels, restrained blue accent (`#6cb8ed`), cyan frame A, amber frame B, violet sequence. Color is always backed by labels for accessibility.
- Windows-native Segoe UI text and Consolas/Cascadia Code for coordinate/time data. No bundled font assets.
- Fine borders and readable density, with predictable 4px control corners rather than oversized floating cards or glassmorphism.
- Toolbar/viewport kept separate from dataset provenance. The navigation relies on semantic buttons, labels, and accessible dialog.
- On small screens the inspector flows beneath the viewer; wide-screen scientific interpretation remains the priority.

## Ethics / attribution

- **Original implementation**. Do not reproduce the Arcsecond UI from the supplied inspiration image, any NASA/ESA logos, or third-party artwork without a valid license.
- Mission data credits: NASA / JPL-Caltech / IPAC, using real releases through official services.
- Reference sky atlas: CDS Aladin Lite; reference survey must be labelled distinctly from SPHEREx.
- No fake images or measurements, misleading certainty, dark patterns, or fabricated discovery claims. Always show when a source, band, detector or calibration is not verified.
- Metadata-only wavelength strips are **not spectra**. The WCS-registered image previews are **not** scientifically certified difference photometry.

## Beginner flow

1. On Windows double-click `run_windows.bat` and open `http://127.0.0.1:8000`.
2. In **Explore**, choose one of the five challenge objects, then set release/survey and select **Find observations**.
3. If public image records are available, the **Frames** panel and **Epoch timeline** populate. Click `A` and `B` on two observations from different dates.
4. Use Blink, Split, B−A or Mean; for a time sequence select up to eight records using `+` and then Sequence.
5. Review UTC baseline, reported wavelength ranges and flags. Download an image preview and evidence JSON with original observation IDs and limitations.
6. The **Atlas** tab is a separate reference survey and should not be described as a SPHEREx measurement.

## Validation

The UI was opened in headless Chromium with CSS/JS inlined from the actual shipped sources (to avoid workspace navigation/network restrictions). The screenshot in `interface-v0.3-desktop.png` captures the real idle state, and the mobile screenshot captures the responsive variant. Browser actions verified reference-target changing, navigation to the reference atlas, help dialog open/close, and return to the SPHEREx tab; no JS errors were reported. The 20 offline tests passed. External archives and FITS processing were not available for end-to-end validation.
