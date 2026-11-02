from fastapi.testclient import TestClient
from backend.app import app

client=TestClient(app)

def test_health_and_static_page():
    body=client.get('/api/health').json()
    assert body['data_policy']=='real_archive_only'
    page=client.get('/')
    assert page.status_code==200
    assert 'Your next discovery starts with a field' in page.text
    assert 'Timeline will display archive timestamps' in page.text
    assert 'SPHEREx Motion Explorer' in page.text

def test_reject_invalid_coordinates_before_network():
    for path in ['/api/observations?ra=-1&dec=0', '/api/observations?ra=15&dec=91',
                 '/api/observations?ra=15&dec=25&fov=90']:
        assert client.get(path).status_code==422

def test_reject_invalid_image_source_without_download():
    r=client.get('/api/render',params={'ra':200,'dec':25,'fov':5,
                                        'a':'not a valid token','mode':'a'})
    assert r.status_code==422
