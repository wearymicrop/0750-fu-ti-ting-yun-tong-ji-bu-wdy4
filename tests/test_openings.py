from concurrent.futures import ThreadPoolExecutor

from app.modules.openings.verdict import adjudicate
from app.modules.reports.manifest import sha256
from app.pipeline import evaluate


def _statuses(result):
    return {row['device']: row['status'] for row in adjudicate(result)['devices']}


def _findings(result, device):
    row = next(item for item in adjudicate(result)['devices'] if item['device'] == device)
    return {(item['code'], item['severity']) for item in row['findings']}


def test_dirty_devices_are_never_released_with_doubts(dirty):
    verdict = adjudicate(evaluate(dirty))
    assert verdict['summary'] == {'OPEN': 0, 'SUSPEND': 2, 'REVIEW': 0}
    assert _statuses(evaluate(dirty)) == {'001': 'SUSPEND', '002': 'SUSPEND'}
    assert _findings(evaluate(dirty), '001') == {
        ('OPEN_OUTAGE', 'SUSPEND'), ('APPROVAL_GAP', 'REVIEW')}
    device_two = next(item for item in verdict['devices'] if item['device'] == '002')
    codes = {item['code'] for item in device_two['findings']}
    assert {'MAINTENANCE_UNAPPROVED', 'MISSING_EVIDENCE', 'REPORT_CONFLICT'} <= codes


def test_open_outage_finding_keeps_event_line_and_detail(dirty):
    device = next(item for item in adjudicate(evaluate(dirty))['devices'] if item['device'] == '001')
    outage = next(item for item in device['findings'] if item['code'] == 'OPEN_OUTAGE')
    assert outage['lines'] == [3] and outage['severity'] == 'SUSPEND'
    assert outage['raw']['winner_line'] == 3 and '未恢复' in outage['detail']


def test_conflict_merged_per_report_code_with_all_lines(dirty):
    device = next(item for item in adjudicate(evaluate(dirty))['devices'] if item['device'] == '002')
    conflict = next(item for item in device['findings'] if item['code'] == 'REPORT_CONFLICT')
    assert conflict['lines'] == [8, 9] and len(conflict['raw']) == 2


def test_clean_sample_releases_every_device(clean):
    verdict = adjudicate(evaluate(clean))
    assert verdict['summary'] == {'OPEN': 2, 'SUSPEND': 0, 'REVIEW': 0}
    assert all(not item['findings'] for item in verdict['devices'])


def test_review_only_doubt_does_not_suspend(clean):
    # 同报码冲突属于待复核，不应直接暂停，但也不能开放
    clean['events'].append({**clean['events'][1], 'start': '2026-11-20T00:10:00+08:00'})
    verdict = adjudicate(evaluate(clean))
    assert verdict['summary'] == {'OPEN': 1, 'SUSPEND': 0, 'REVIEW': 1}
    assert _statuses(evaluate(clean))['002'] == 'REVIEW'


def test_unapproved_maintenance_suspends(clean):
    clean['permits'].append({
        'device': '002', 'id': 'P-HOLD', 'start': '2026-11-19T23:00:00+08:00',
        'end': '2026-11-20T00:30:00+08:00', 'reason': 'MAINTENANCE',
        'status': 'pending', 'approval': None})
    assert _statuses(evaluate(clean))['002'] == 'SUSPEND'


def test_device_without_service_window_is_review(clean):
    clean['shifts'] = [row for row in clean['shifts'] if row['device'] != '002']
    result = evaluate(clean)
    verdict = adjudicate(result)
    assert _statuses(result)['002'] == 'REVIEW'
    assert _findings(result, '002') == {('NO_SERVICE', 'REVIEW')}


def test_verdict_is_deterministic(dirty):
    first = adjudicate(evaluate(dirty))
    second = adjudicate(evaluate(dirty))
    assert first == second


def _open(client, sample='dirty'):
    report = client.post('/api/runs', json={'sample': sample}).json()
    return report, client.post(f"/api/runs/{report['id']}/openings", json={}).json()


def test_create_opening_persists_per_device_verdict(client):
    report, batch = _open(client)
    assert batch['reused'] is False
    assert batch['report_id'] == report['id']
    assert [row['device'] for row in batch['devices']] == ['001', '002']
    stored = client.get(f"/api/runs/{report['id']}/openings").json()
    assert stored['devices'] == batch['devices']
    assert stored['manifest'] == batch['manifest']


def test_rerun_same_batch_does_not_change_or_add_conclusion(client):
    report, first = _open(client)
    again = client.post(f"/api/runs/{report['id']}/openings", json={}).json()
    third = client.post(f"/api/runs/{report['id']}/openings", json={}).json()
    assert again['reused'] is True and third['reused'] is True
    assert again['manifest']['digest'] == first['manifest']['digest']
    assert again['devices'] == first['devices']
    assert len(client.get('/api/openings').json()['openings']) == 1


def test_concurrent_openings_commit_once(client):
    report = client.post('/api/runs', json={'sample': 'clean'}).json()
    with ThreadPoolExecutor(max_workers=4) as executor:
        copies = list(executor.map(
            lambda _: client.post(f"/api/runs/{report['id']}/openings", json={}).json(), range(4)))
    assert len({batch['manifest']['digest'] for batch in copies}) == 1
    assert sum(not batch['reused'] for batch in copies) == 1


def test_export_matches_page_and_keeps_full_doubts(client):
    report, batch = _open(client)
    response = client.get(f"/api/runs/{report['id']}/openings/export")
    assert response.headers['content-disposition'].startswith('attachment;')
    payload = response.json()
    assert payload['batch']['devices'] == batch['devices']
    assert payload['batch']['summary'] == batch['summary']
    assert sha256(payload['input']) == report['manifest']['input_sha256']
    # 任何疑点都要完整留档：暂停依据与原始值均在下载件中
    device_two = next(row for row in payload['batch']['devices'] if row['device'] == '002')
    assert all(finding['raw'] for finding in device_two['findings'])
    assert any(item['code'] == 'REPORT_CONFLICT' and item['lines'] == [8, 9]
               for item in device_two['findings'])


def test_opening_requires_archived_report(client):
    response = client.post('/api/runs/missing/openings', json={})
    assert response.status_code == 404 and response.json()['code'] == 'REPORT_NOT_FOUND'
    response = client.get('/api/runs/missing/openings')
    assert response.status_code == 404 and response.json()['code'] == 'REPORT_NOT_FOUND'
    # 班报已归档但尚未形成开放记录时，给出独立的未找到码
    report = client.post('/api/runs', json={'sample': 'clean'}).json()
    response = client.get(f"/api/runs/{report['id']}/openings")
    assert response.status_code == 404 and response.json()['code'] == 'OPENING_NOT_FOUND'
    response = client.get(f"/api/runs/{report['id']}/openings/export")
    assert response.status_code == 404 and response.json()['code'] == 'OPENING_NOT_FOUND'


def test_opening_list_reports_summaries(client):
    _, dirty_batch = _open(client, 'dirty')
    client.post('/api/runs', json={'sample': 'clean'}).json()
    clean_report = client.post('/api/runs', json={'sample': 'clean'}).json()
    client.post(f"/api/runs/{clean_report['id']}/openings", json={})
    openings = client.get('/api/openings').json()['openings']
    assert len(openings) == 2
    by_id = {item['report_id']: item for item in openings}
    assert by_id[dirty_batch['report_id']]['summary'] == {'OPEN': 0, 'SUSPEND': 2, 'REVIEW': 0}


def test_retries_keep_records_after_failed_attempts(client):
    report = client.post('/api/runs', json={'sample': 'clean'}).json()
    # 不存在的班报开放失败，不得影响后续正常留档
    client.post('/api/runs/never-existed/openings', json={})
    batch = client.post(f"/api/runs/{report['id']}/openings", json={}).json()
    assert batch['reused'] is False and batch['summary']['OPEN'] == 2
    assert client.get(f"/api/runs/{report['id']}/openings").status_code == 200
