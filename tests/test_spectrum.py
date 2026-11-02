"""Aperture photometry and wavelength-interpolation units on synthetic frames.

Synthetic numerical fixtures are used strictly inside unit tests; they are
never displayed to users as sky images.
"""
import base64
import io
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

from backend import science, spectrum
from backend.science import local_wavelength, ScienceError


def synthetic_hdul(flux=500.0, target_xy=(12, 10), shape=(20, 24), lam_slope=0.0005):
    """A 2-D frame with a gaussian source, flat variance, and a 9x9 wave grid."""
    tx, ty = target_xy
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    image = 10.0 + flux * np.exp(-((xx - tx) ** 2 + (yy - ty) ** 2) / (2 * 1.2 ** 2))
    image[5, 5] = np.nan                      # one dead pixel
    flags = np.zeros(shape, dtype=np.int32)
    flags[5, 5] = 1 << 6                      # NONFUNC
    flags[ty, tx] = 1 << 21                   # SOURCE on the star
    variance = np.full(shape, 4.0)
    zodi = np.full(shape, 2.5)
    grid = np.linspace(1, shape[1], 9)
    wv = {'X': grid.astype(float), 'Y': np.linspace(1, shape[0], 9).astype(float),
          'VALUES': np.stack([3.0 + lam_slope * (grid[None, :] - 1) * np.ones((9, 9)),
                              np.full((9, 9), 0.02)])}
    hdul = fits.HDUList([
        fits.PrimaryHDU(),
        fits.ImageHDU(image.astype(np.float32), name='IMAGE'),
        fits.ImageHDU(flags, name='FLAGS'),
        fits.ImageHDU(variance.astype(np.float32), name='VARIANCE'),
        fits.ImageHDU(zodi.astype(np.float32), name='ZODI'),
    ])
    # Simple TAN celestial WCS centred on the target position.
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [tx + 1, ty + 1]
    wcs.wcs.cdelt = [-6.2 / 3600, 6.2 / 3600]
    wcs.wcs.crval = [269.446, 4.771]
    wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    hdul[0].header.update(wcs.to_header())
    for card in list(hdul[1].header.keys()):
        pass
    hdul[1].header.update(wcs.to_header())
    hdul[1].header['CRPIX1A'] = 0.0   # synthetic A-WCS: detector coords == cutout coords
    hdul[1].header['CRPIX2A'] = 0.0
    hdul[1].header['BUNIT'] = 'MJy/sr'
    return hdul, image, flags, variance, wv


def fake_open_cutout(monkeypatch, hdul, image, flags, variance, wv):
    def _open(source, ra, dec, fov):
        return {'header': hdul[1].header, 'data': image.astype(np.float64),
                'wcs': WCS(hdul[1].header).celestial, 'flags': flags,
                'variance': variance, 'zodi': None,
                'wave_table': wv, 'hdul': hdul}
    monkeypatch.setattr(spectrum, 'open_cutout', _open)


def test_extract_point_aperture_flux(monkeypatch):
    hdul, image, flags, variance, wv = synthetic_hdul(flux=500.0)
    fake_open_cutout(monkeypatch, hdul, image, flags, variance, wv)
    point = spectrum.extract_point('https://irsa.ipac.caltech.edu/ibe/data/spherex/qr/level2/x_3D3_spx.fits',
                                   269.446, 4.771, 4.0)
    # Gaussian sigma=1.2px: r<=2 encloses ~75% of 500*2*pi*1.44 -> ~3400 above bkg.
    assert 2500 < point['flux_MJy_sr'] < 4000
    assert point['aperture_pixels'] >= 9
    assert point['err_stat_MJy_sr'] > 0
    assert abs(point['lambda_um'] - 3.0) < 0.01      # linear grid at target column
    assert point['detector'] == 'D3'


def test_extract_point_rejects_out_of_frame(monkeypatch):
    hdul, image, flags, variance, wv = synthetic_hdul()
    fake_open_cutout(monkeypatch, hdul, image, flags, variance, wv)
    try:
        spectrum.extract_point('https://irsa.ipac.caltech.edu/ibe/data/spherex/qr/level2/x_D1.fits',
                               10.0, 70.0, 4.0)
    except ScienceError:
        pass
    else:
        raise AssertionError('Out-of-frame target accepted.')


def test_local_wavelength_interpolates_linear_grid():
    hdul, image, flags, variance, wv = synthetic_hdul()
    wcs = WCS(hdul[1].header).celestial
    wave = local_wavelength(hdul[1].header, wv, wcs, 269.446, 4.771)
    assert wave['reason'] == 'ok'
    assert abs(wave['lambda_um'] - 3.0) < 0.01
    assert wave['bandwidth_um'] == 0.02


def test_sample_files_evenly_across_wavelength():
    rows = [{'source': f'https://irsa.ipac.caltech.edu/ibe/data/spherex/qr/level2/f{i}_D1.fits',
             'wavelength_min_um': float(i)} for i in range(100)]
    sample = spectrum._sample_files(rows, 10)
    assert len(sample) == 10
    picked = [r['wavelength_min_um'] for r in sample]
    assert picked == sorted(picked)
    assert picked[0] == 0.0 and picked[-1] > 80   # spans the full range
