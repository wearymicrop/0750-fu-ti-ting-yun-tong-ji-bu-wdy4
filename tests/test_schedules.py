import pytest

from app.pipeline import evaluate
from app.times import instant


def test_midnight_shift(clean):
    # TRAP-23
    east = evaluate(clean, 'schedules')['devices']['001']['windows'][0]
    assert east['end'] == instant('2026-11-20T02:00:00+08:00')
    assert east['seconds'] == 18000


def test_overlapping_shifts_are_unioned(dirty):
    # TRAP-25
    east = evaluate(dirty, 'schedules')['devices']['001']
    assert sum(item['seconds'] for item in east['windows']) == 25200
    assert [row['line'] for row in east['shifts']] == [1, 3, 4]


def test_device_preserves_leading_zero(dirty):
    # TRAP-08
    assert list(evaluate(dirty, 'schedules')['devices']) == ['001', '002']


def test_unknown_device_shift(dirty):
    # TRAP-21
    assert {'line': 5, 'code': 'UNKNOWN_DEVICE', 'raw': dirty['shifts'][4]} in evaluate(dirty, 'schedules')['shift_issues']


def test_equal_clock_is_invalid(dirty):
    assert evaluate(dirty, 'schedules')['shift_issues'][1]['code'] == 'INVALID_SHIFT'


def test_adjacent_shifts_have_no_gap(clean):
    clean['shifts'].append({'device': '001', 'day': '2026-11-20', 'from': '02:00:00', 'to': '03:00:00'})
    east = evaluate(clean, 'schedules')['devices']['001']['windows']
    assert len(east) == 1 and east[0]['seconds'] == 21600


def test_duplicate_device_is_ambiguous(clean):
    clean['devices'].append({'device': '001', 'name': '南厅'})
    out = evaluate(clean, 'schedules')
    assert list(out['devices']) == ['002']
    assert {row['line'] for row in out['device_issues']} == {1, 3}


def test_fractional_or_naive_windows_rejected(client, clean):
    clean['start'] = '2026-11-19T20:00:00.2'
    response = client.post('/api/runs', json={'data': clean})
    assert response.status_code == 422 and response.json()['code'] == 'INVALID_WINDOW'
