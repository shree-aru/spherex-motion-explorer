"""Official SPHEREx L2b FLAGS bit semantics.

Source: SPHEREx Explanatory Supplement SSDC-DP-017 v2.0 (2026-08-25),
data-product flag table (doc pages 31-32) and section 3.4.9 (mosaic bad-flag
handling).  FLAGS is a 32-bit *status bitmap*, not a 0=good mask: masking
every non-zero pixel erases bit 21 (SOURCE), i.e. every star in the field.
"""
from __future__ import annotations

import numpy as np

FLAG_DEFINITIONS: dict[int, tuple[str, str]] = {
    0:  ("TRANSIENT",      "Transient event detected during SUR (e.g. cosmic ray)."),
    1:  ("OVERFLOW",       "Overflow threshold reached during SUR (saturation/bloom core)."),
    2:  ("SUR_ERROR",      "SUR checksum/error bit from instrument data processing."),
    6:  ("NONFUNC",        "Pixel non-functional (static pre-flight assessment)."),
    7:  ("DICHROIC",       "Low-efficiency dichroic 'dark corner' of bands 3/4."),
    9:  ("MISSING_DATA",   "Onboard data lost before download."),
    10: ("HOT",            "Hot / spuriously noisy pixel."),
    11: ("COLD",           "Pixel apparently unresponsive to light."),
    12: ("FULLSAMPLE",     "Full sample history available (informational)."),
    14: ("PHANMISS",       "Pixel not correctable due to missing phantom pixels."),
    15: ("NONLINEAR",      "Nonlinearity correction unreliable; exclude from science."),
    17: ("PERSIST",        "Affected by persistence above the Level 2 threshold."),
    19: ("OUTLIER",        "Flagged by the outlier-pixel detection module."),
    20: ("CROSSTALK",      "Affected by ordinary electronic crosstalk."),
    21: ("SOURCE",         "Pixel mapped to a known source (flux-bearing; keep visible)."),
    22: ("GHOST",          "Affected by an optical ghost."),
    23: ("GHOST_FPA",      "Affected by a focal-plane-array optical ghost."),
    24: ("GHOST_EXT",      "Affected by an external optical ghost."),
    25: ("STREAK",         "Crossed by a streak from an Earth-orbiting object."),
    26: ("BLOOM",          "Affected by source blooming."),
    27: ("SNOWBALL",       "Affected by a snowball artifact."),
    28: ("HALO",           "Affected by the halo of a snowball or transient."),
    29: ("SATELLITE_HALO", "Affected by the halo of a saturating satellite streak."),
}

# Bits that mark a pixel unusable for display or photometry.  Mirrors the
# L2 mosaic bad-flag practice (supplement section 3.4.9 keeps SOURCE
# propagated but treats it as an informational, flux-bearing status).
FATAL_BITS = frozenset({0, 1, 2, 6, 7, 9, 10, 11, 14, 15, 17, 19,
                        20, 22, 23, 24, 25, 26, 27, 28, 29})
# Informational bits that carry signal or benign state and must stay visible.
VISIBLE_BITS = frozenset({12, 21})
# For visual frames only: saturated/bloomed cores stay visible so bright
# stars do not turn into holes; detector-dead pixels are still removed.
DISPLAY_FATAL_BITS = frozenset({6, 9, 10, 11, 14})

FATAL_MASK = sum(1 << bit for bit in FATAL_BITS)
DISPLAY_FATAL_MASK = sum(1 << bit for bit in DISPLAY_FATAL_BITS)


def fatal_mask(flags: np.ndarray, level: str = 'strict') -> np.ndarray:
    """Boolean mask of pixels carrying at least one fatal bit.

    level='display' keeps saturation-family pixels visible for visual frames;
    level='strict' masks everything the supplement calls bad.
    """
    mask = DISPLAY_FATAL_MASK if level == 'display' else FATAL_MASK
    return (np.asarray(flags).astype(np.int64) & mask) != 0


def summarize_flags(flags: np.ndarray) -> dict:
    """Per-bit pixel fractions plus the fatal/kept totals for provenance."""
    flat = np.asarray(flags).astype(np.int64).ravel()
    total = int(flat.size)
    per_bit = {}
    for bit, (name, _) in FLAG_DEFINITIONS.items():
        count = int(np.count_nonzero(flat & (1 << bit)))
        if count:
            per_bit[name] = {'bit': bit, 'fraction': round(count / total, 6)}
    return {
        'total_pixels': total,
        'fatal_fraction': round(float(np.mean((flat & FATAL_MASK) != 0)), 6),
        'source_flag_fraction': round(float(np.mean((flat & (1 << 21)) != 0)), 6),
        'bits_present': per_bit,
    }
