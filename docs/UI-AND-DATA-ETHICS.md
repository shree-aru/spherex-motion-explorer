# Originality, professional UX, and observational ethics

The public tool must look and behave like a **real astronomical instrument**, not like a generic AI-generated dashboard or a copy of a NASA, ESA, or CDS interface.

## Design principles

1. **No cloning:** original layout, typography hierarchy, controls, brand mark, spacing and written microcopy. Aladin Lite is a credited, licensed embedded visualization component, not a design template.
2. **Data first:** the sky image dominates the layout. Graphs and colors must encode actual information; empty states show no decorative fake stars. All survey references are explicitly named.
3. **Provenance everywhere:** archive, dataset release, exposure dates, wavelengths, detector, processing mode, masked flags, software version and uncertainty limitations.
4. **Interpretation must be reversible:** blink, split and subtraction should use consistent grids and clearly marked sign conventions; raw FITS are never silently changed.
5. **Respect the visitor:** accessible labels, keyboard controls, adjustable blink speed, reduced-motion preference, no deceptive discovery scores, no engagement dark patterns.
6. **Honest uncertainty:** no automatic 'new planet', 'brown dwarf discovered' or 'science-grade spectrum' labels. A potentially moving point becomes a **candidate** awaiting catalogue checks and corroboration.
7. **No unlicensed copying:** trace licenses of fonts, scientific packages, icons and imagery. Keep official data acknowledgements and library attributions.

## Implemented visual system

A near-black neutral canvas (`#0d1115`), graphite rails, restrained blue-grey focus color, intentionally narrow UI typography, monospace measurement values and scientific labels. A small, original orbital line-mark replaces borrowed mission insignia. No nonfunctional animated galaxies, neon gradients, fake 3-D planet art, stock space photos or glassmorphism. The interface is intentionally calm, dense and testable.

## Data truth labels

- **Reference atlas:** displays independent DSS2 or other Aladin-served imagery. It must never be labelled SPHEREx.
- **SPHEREx frames:** renders only actual FITS from IRSA when reachable.
- **Difference:** currently a registered **visual residual**. No PSF matching, wavelength equality check or reliable significance calculation. This is neither a validated detection nor a publishable flux measurement.
- **Input centre:** high-proper-motion object coordinates are first-order approximations based on catalog motion; they do not include parallax or full space motion. ε Indi B uses J2000 coordinate without an orbital solution.

## Human evaluation protocol

Conduct hands-on tests with (1) a novice visitor, (2) an astronomy enthusiast and (3) an astrophysics researcher. Ask them to retrieve Barnard's Star, choose two actual epochs, compare movement, identify which imagery is from SPHEREx, locate release metadata, and explain why a bright difference residual could be instrumental. Track task completion, errors, time to understand caveats and accessibility issues. Revise before claiming a research-ready product.
