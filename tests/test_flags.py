"""Official SPHEREx flag-bit semantics, verified against the Explanatory Supplement."""
import numpy as np

from backend.flags import FATAL_MASK, fatal_mask, summarize_flags


def test_source_flag_is_not_fatal():
    # Bit 21 = SOURCE: flux-bearing pixels of real stars must stay visible.
    flags = np.array([[0, 1 << 21], [1 << 21 | 1 << 6, 1 << 15]], dtype=np.int64)
    masked = fatal_mask(flags)
    assert masked[0, 0] == False
    assert masked[0, 1] == False          # SOURCE only -> visible
    assert masked[1, 0] == True           # NONFUNC present -> fatal
    assert masked[1, 1] == True           # NONLINEAR -> fatal


def test_real_world_dominant_value_is_kept():
    # Most common value in real QR3 cutouts: 2097152 = SOURCE only.
    assert (FATAL_MASK & (1 << 21)) == 0
    assert fatal_mask(np.array([[2_097_152]]))[0, 0] == False


def test_fatal_bits_cover_instrument_issues():
    for name_value in ('OVERFLOW', 'SAT'):
        pass
    for bit in (0, 1, 2, 6, 15, 17, 19, 25, 27, 28):
        assert FATAL_MASK & (1 << bit), f'bit {bit} must be fatal'


def test_summarize_reports_source_separately():
    flags = np.array([[1 << 21] * 3 + [0]], dtype=np.int64)
    summary = summarize_flags(flags)
    assert summary['fatal_fraction'] == 0.0
    assert summary['source_flag_fraction'] == 0.75
    assert 'SOURCE' in summary['bits_present']
