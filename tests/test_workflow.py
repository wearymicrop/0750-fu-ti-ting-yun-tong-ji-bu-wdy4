from app.times import instant


def test_full_sample_workflow(client):
    home = client.get('/')
    assert home.status_code == 200 and home.text.count('data-section=') == 7
    assert client.get('/healthz').json()['service'] == 'lift-duties'
    for stage, field in [('schedules', 'devices'), ('events', 'counts'), ('clipping', 'pieces'),
                         ('attribution', 'segments'), ('exemptions', 'permits'), ('reconcile', 'totals')]:
        response = client.get(f'/api/{stage}/dirty')
        assert response.status_code == 200 and field in response.json()
    instant_start = instant('2026-11-19T22:30:00+08:00')
    data = client.get('/api/preview/dirty/evidence', params={'device': '001', 'start': instant_start}).json()
    assert data['segment']['bucket'] == 'exempt' and [row['id'] for row in data['permits']] == ['P-101', 'P-102']


def test_bad_sample_and_empty_input(client):
    sample = client.get('/api/reconcile/no-such-sample')
    assert sample.status_code == 404 and sample.json()['code'] == 'SAMPLE_NOT_FOUND'
    run = client.post('/api/runs', json={})
    assert run.status_code == 422 and run.json()['code'] == 'CHOOSE_SOURCE'
