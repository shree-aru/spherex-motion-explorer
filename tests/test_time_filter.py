"""UTC observation-window tests without calling the archive."""
from datetime import date
from fastapi.testclient import TestClient
from backend.app import app
from backend.archive import mjd_from_date
from backend import app as api_module

client = TestClient(app)


def test_mjd_from_utc_day():
    assert mjd_from_date(date(1858, 11, 17)) == 0.0
    assert mjd_from_date(date(2025, 5, 1)) > 60000
    assert mjd_from_date(date(2025, 5, 2))-mjd_from_date(date(2025, 5, 1)) == 1.0


def test_api_rejects_invalid_utc_window():
    r = client.get('/api/observations?ra=133&dec=4&start_date=2026-05-01&end_date=2025-05-01')
    assert r.status_code == 422
    assert 'start date' in r.json()['detail'].lower()


def test_date_filters_passed_to_archive(monkeypatch):
    seen = {}
    def fake_query(*args, **kwargs):
        seen.update(kwargs)
        return {'observations': [], 'archive_count': 0, 'result_limit': 600,
                'may_be_truncated': False, 'query_url': 'https://irsa.ipac.caltech.edu/SIA', 'note': 'test'}
    monkeypatch.setattr(api_module, 'search_observations', fake_query)
    response = client.get('/api/observations?ra=133&dec=4&start_date=2025-05-01&end_date=2026-10-30')
    assert response.status_code == 200
    assert seen['start_date'] == date(2025, 5, 1)
    assert seen['end_date'] == date(2026, 10, 30)


def test_sia_params_for_qr3_deep_and_closed_time_window(monkeypatch):
    from backend import archive
    class Response:
        text = 'access_url,obs_id,t_min,em_min,em_max\n'
        def raise_for_status(self):
            return None
    class MockClient:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def get(self, url, params):
            assert url == 'https://irsa.ipac.caltech.edu/SIA'
            assert params['COLLECTION'] == 'spherex_qr3_deep'
            assert params['DPTYPE'] == 'image'
            assert params['CALIB'] == '2'
            lo, hi = [float(x) for x in params['TIME'].split()]
            assert lo == mjd_from_date(date(2025, 5, 1))
            assert hi == mjd_from_date(date(2025, 5, 3))
            return Response()
    monkeypatch.setattr(archive.httpx, 'Client', MockClient)
    result = archive.search_observations(269, 4, 7, survey='deep', release='qr3',
                                         start_date=date(2025, 5, 1), end_date=date(2025, 5, 2))
    assert result['survey'] == 'deep'
    assert result['observations'] == []
