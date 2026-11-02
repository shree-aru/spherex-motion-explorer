# Competition readiness and judge plan

## Positioning

SPHEREx Motion Explorer is an independent public investigation workbench for comparing real SPHEREx archive epochs. It is not official NASA software and it does not certify discoveries. Its differentiators are archive provenance, an explicit temporal-coverage workflow, detector-aware comparison guidance, reversible image views, and evidence export.

## Golden-path demonstration

1. Choose a target with confirmed live archive coverage, preferably Barnard's Star or the target supplied in the official resources.
2. Search the official NASA/IPAC IRSA SIA endpoint and show the returned record count, earliest epoch, latest epoch, and baseline summary.
3. Press **Use widest baseline**. The application chooses the earliest and latest dated observations sharing a detector label; it does not silently mix detector ranges.
4. Show the two real FITS-derived frames in Split and Blink modes. Show UTC, detector, wavelength metadata, flagged-pixel fractions, and the scientific caution card.
5. Open **B − A** only as an exploratory residual. Explain that PSF, local wavelength, calibration, and uncertainty matching are not yet certified.
6. Point to the human-review cues. They are percentile-thresholded display-pixel regions for inspection, not discovery scores, motion measurements, or significance values.
7. Export the Evidence JSON and open the shared view URL. Explain that the result is reproducible from official archive identifiers and recorded processing warnings.

## Required evidence before submission

- At least one real SIA response saved with its query URL and timestamp.
- At least one real FITS cutout saved with source URL, observation identifier, release DOI, and SHA-256.
- A screenshot or recording showing two real rendered epochs.
- A documented explanation of whether the pair is appropriate for visual comparison.
- A clean-machine run on Windows or Linux with the declared dependency installer.
- A fallback demo field if the first target has no coverage or the archive is temporarily unavailable.

## Claims the team may make

- The tool retrieves public SPHEREx archive records from NASA/IPAC IRSA.
- It aligns returned FITS imagery onto a common visual WCS grid.
- It makes temporal changes easier for a human to inspect.
- It reports provenance and processing cautions.
- It provides exploratory residual cues to prioritize human review.

## Claims the team must not make yet

- A residual is a confirmed moving object, transient, planet, comet, or brown dwarf.
- The B − A image is calibrated difference photometry.
- Detector-level wavelength ranges are identical at every pixel.
- The application has measured motion significance or a validated discovery classifier.
- An empty archive response means the target is absent from the sky.

## Backup plan

If IRSA is unavailable during judging, show the live error state and the official query URL, then use a previously verified real-data recording or a legally redistributable FITS fixture clearly labelled as an archive-derived validation artifact. Never substitute generated or invented sky imagery.

