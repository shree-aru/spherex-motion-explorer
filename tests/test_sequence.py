"""Synthetic *numerical* fixtures only; the public UI never presents test data."""
import base64
import io
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from backend import science
from backend import app as api_module

client = TestClient(api_module.app)
SOURCE_A = 'https://irsa.ipac.caltech.edu/ibe/data/spherex/qr/level2/a.fits'
SOURCE_B = 'https://irsa.ipac.caltech.edu/ibe/data/spherex/qr/level2/b.fits'
SOURCE_C = 'https://irsa.ipac.caltech.edu/ibe/data/spherex/qr/level2/c.fits'


def source_token(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')


def frame_for(source, *_):
    i = [SOURCE_A, SOURCE_B, SOURCE_C].index(source)
    a = np.array([[1., 2.], [3., 8.]], dtype=float)
    a[0, 0] = (i + 1)*9
    return a, {'source_url': source, 'bunit': 'MJy/sr', 'flagged_input_fraction': 0,
               'valid_output_fraction': 1, 'processing': 'test only'}


def test_sequence_same_stretch_and_order(monkeypatch):
    monkeypatch.setattr(science, 'aligned_frame', frame_for)
    images, meta = science.render_sequence([SOURCE_A, SOURCE_B, SOURCE_C], 1, 2, 3)
    assert len(images) == 3
    assert meta['display_stretch']['high'] > meta['display_stretch']['low']
    assert meta['scientific_level'] == 'exploratory_previews_only'
    assert all(Image.open(io.BytesIO(img)).mode == 'RGBA' for img in images)
    sample_intensities = [np.asarray(Image.open(io.BytesIO(x)))[1, 0, 0] for x in images]
    assert sample_intensities == sorted(sample_intensities)
    assert len(set(int(x) for x in sample_intensities)) == 3


def test_sequence_error_cases(monkeypatch):
    monkeypatch.setattr(science, 'aligned_frame', frame_for)
    for sources in [[SOURCE_A], [SOURCE_A, SOURCE_A], [SOURCE_A]*9]:
        try:
            science.render_sequence(sources, 0, 0, 3)
        except science.ScienceError:
            pass
        else:
            raise AssertionError('Rejected input was accepted.')


def test_sequence_api_never_fetches_untrusted_url():
    payload = {'ra': 11., 'dec': -2., 'fov': 8.,
               'tokens': [source_token(SOURCE_A), source_token('https://evil.example/bad.fits')]}
    response = client.post('/api/sequence', json=payload)
    assert response.status_code == 422
    assert 'untrusted' in response.json()['detail'].lower()


def test_sequence_api_response(monkeypatch):
    monkeypatch.setattr(science, 'aligned_frame', frame_for)
    payload = {'ra': 11., 'dec': -2., 'fov': 8.,
               'tokens': [source_token(SOURCE_A), source_token(SOURCE_B)]}
    response = client.post('/api/sequence', json=payload)
    assert response.status_code == 200
    result = response.json()
    assert len(result['images_base64']) == 2
    assert result['metadata']['frames'][0]['source_url'] == SOURCE_A
    assert base64.b64decode(result['images_base64'][0]).startswith(b'\x89PNG')


def test_sequence_api_rejects_bad_coordinate():
    payload = {'ra': 370., 'dec': -2., 'fov': 8.,
               'tokens': [source_token(SOURCE_A), source_token(SOURCE_B)]}
    assert client.post('/api/sequence', json=payload).status_code == 422
