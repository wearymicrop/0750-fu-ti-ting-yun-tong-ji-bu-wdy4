from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app
from app.modules.reports.manifest import sha256


def test_rerun_same_id_and_digest(client):
    first = client.post('/api/runs', json={'sample': 'dirty'}).json()
    again = client.post(f"/api/runs/{first['id']}/rerun").json()
    assert again['reused'] is True
    assert (again['id'], again['manifest']['digest']) == (first['id'], first['manifest']['digest'])


def test_duplicate_posts_commit_once(client):
    with ThreadPoolExecutor(max_workers=4) as executor:
        copies = list(executor.map(lambda _: client.post('/api/runs', json={'sample': 'clean'}).json(), range(4)))
    assert len({report['id'] for report in copies}) == 1
    assert sum(not report['reused'] for report in copies) == 1
    assert len(client.get('/api/runs').json()['runs']) == 1


def test_attachment_has_raw_and_digest(client):
    report = client.post('/api/runs', json={'sample': 'dirty'}).json()
    response = client.get(f"/api/runs/{report['id']}/export")
    assert response.headers['content-disposition'].startswith('attachment;')
    data = response.json()
    assert data['input']['events'][5]['start'].endswith('Z')
    assert sha256(data['input']) == report['manifest']['input_sha256']
    assert sha256(data['result']) == report['manifest']['digest']


def test_persists_across_client_lifetimes(client):
    report = client.post('/api/runs', json={'sample': 'clean'}).json()
    with TestClient(app) as later:
        result = later.get(f"/api/runs/{report['id']}").json()
    assert result['manifest'] == report['manifest'] and result['result'] == report['result']


def test_evidence_includes_winner_loser_and_retransmission(client):
    report = client.post('/api/runs', json={'sample': 'dirty'}).json()
    row = next(row for row in report['result']['segments'] if row['event_lines'] == [2, 5, 6])
    response = client.get(f"/api/runs/{report['id']}/evidence", params={'device': '001', 'start': row['start']})
    data = response.json()
    assert [event['id'] for event in data['events'] if event['winner']] == ['E-102']
    assert [row['line'] for row in data['retransmissions']] == [6]
    assert [row['line'] for row in data['shifts']] == [1]


def test_same_custom_data_with_object_order_reversed(client, clean):
    one = client.post('/api/runs', json={'data': clean}).json()
    two = client.post('/api/runs', json={'data': dict(reversed(list(clean.items())))}).json()
    assert one['id'] == two['id'] and two['reused'] is True


def test_rejected_payload_does_not_leave_partial_report(client, clean):
    clean['shifts'] = None
    response = client.post('/api/runs', json={'data': clean})
    assert response.status_code == 422 and response.json()['code'] == 'INVALID_ROWS'
    assert client.get('/api/runs').json() == {'runs': []}


def test_report_not_found(client):
    response = client.get('/api/runs/missing')
    assert response.status_code == 404 and response.json()['code'] == 'REPORT_NOT_FOUND'
