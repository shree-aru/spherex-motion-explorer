"""Offline tests for archive metadata and data-origin protection."""
from backend.archive import band_for_range, iso_from_mjd, parse_sia_csv, valid_source_url

GOOD = 'https://irsa.ipac.caltech.edu/ibe/data/spherex/qr/level2/x.fits'

def test_trusted_source():
    assert valid_source_url(GOOD)
    for url in [
        'http://irsa.ipac.caltech.edu/ibe/data/spherex/x.fits',
        'https://irsa.ipac.caltech.edu.evil.com/ibe/data/spherex/x.fits',
        'https://irsa.ipac.caltech.edu/ibe/data/spherex/x.fits?redirect=evil',
        'https://irsa.ipac.caltech.edu@evil.com/ibe/data/spherex/x.fits',
        'https://irsa.ipac.caltech.edu/ibe/data/spherex/x.json',
        'file:///etc/passwd',
    ]:
        assert not valid_source_url(url)


def test_sia_csv_filters_other_archives():
    sample = ('access_url,obs_id,t_min,em_min,em_max\n'
              f'{GOOD},test123,60000,0.0000012,0.0000015\n'
              'https://other.example/image.fits,bad,60000,0.0000012,0.0000015\n')
    results = parse_sia_csv(sample, 'qr3')
    assert len(results) == 1
    assert results[0]['obs_id'] == 'test123'
    assert results[0]['band'] == 'D2'
    assert results[0]['release'] == 'QR3'
    assert results[0]['date_utc'].startswith('2023-02-25')


def test_wavelength_ranges_are_not_forced():
    assert band_for_range(0.8, 1.0) == 'D1'
    assert band_for_range(2.5, 3.1) == 'D4'
    assert band_for_range(None, None) == 'Unknown'
    assert iso_from_mjd(0) == '1858-11-17T00:00:00Z'
