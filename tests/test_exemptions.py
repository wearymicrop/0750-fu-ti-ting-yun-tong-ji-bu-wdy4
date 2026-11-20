from app.pipeline import evaluate


def test_overlapping_approvals_count_once(dirty):
    rows = evaluate(dirty, 'exemptions')['segments']
    east = [row for row in rows if row['device'] == '001' and row['bucket'] == 'exempt']
    assert [(row['seconds'], row['permit_lines']) for row in east] == [(1800, [1]), (900, [1, 2]), (900, [2])]


def test_permit_matching_losing_reason_does_not_apply(dirty):
    dirty['permits'][2]['reason'] = 'MECHANICAL'
    dirty['permits'][2]['start'] = '2026-11-19T21:30:00+08:00'
    rows = evaluate(dirty, 'exemptions')['segments']
    assert all(3 not in row['permit_lines'] for row in rows)


def test_pending_only_does_not_apply(dirty):
    rows = evaluate(dirty, 'exemptions')['segments']
    west = [row for row in rows if row['device'] == '002' and row['bucket'] == 'exempt']
    assert [(row['seconds'], row['permit_lines']) for row in west] == [(900, [4])]


def test_missing_approval_is_isolated(dirty):
    result = evaluate(dirty, 'exemptions')
    assert result['isolated'] == [{'line': 6, 'code': 'MISSING_APPROVAL', 'raw': dirty['permits'][5]}]


def test_approved_window_does_not_excuse_available_time(clean):
    clean['permits'][0]['end'] = '2026-11-19T23:40:00+08:00'
    rows = evaluate(clean, 'exemptions')['segments']
    assert sum(row['seconds'] for row in rows if row['bucket'] == 'exempt') == 1800


def test_wildcard_approval_cannot_turn_missing_into_exempt(dirty):
    dirty['permits'][0].update(reason=None, start='2026-11-20T03:00:00+08:00', end='2026-11-20T04:00:00+08:00')
    rows = evaluate(dirty, 'exemptions')['segments']
    row = next(row for row in rows if row['code'] == 'OPEN_EVENT')
    assert row['seconds'] == 3600 and row['permit_lines'] == [] and row['bucket'] == 'missing'


def test_wildcard_approval_is_device_scoped(dirty):
    dirty['permits'][3]['reason'] = None
    rows = evaluate(dirty, 'exemptions')['segments']
    assert [(row['device'], row['seconds']) for row in rows if 4 in row['permit_lines']] == [('002', 900)]
