from app.pipeline import evaluate
from app.times import instant


def test_before_open_does_not_count(dirty):
    result = evaluate(dirty, 'clipping')
    cut = next(row for row in result['pieces'] if row['id'] == 'E-101')
    assert cut['seconds'] == 3600
    assert result['excluded'] == [
        {'line': 2, 'id': 'E-101', 'code': 'NON_SERVICE', 'seconds': 900},
        {'line': 3, 'id': 'E-104', 'code': 'NON_SERVICE', 'seconds': 7200},
    ]


def test_at_closing_is_outside(clean):
    clean['events'][0].update(start='2026-11-20T02:00:00+08:00', end='2026-11-20T03:00:00+08:00')
    result = evaluate(clean, 'clipping')
    assert [row['line'] for row in result['pieces']] == [2]
    assert result['excluded'][0]['seconds'] == 3600


def test_event_wholly_after_cutoff(clean):
    clean['cutoff'] = '2026-11-19T21:00:00+08:00'
    result = evaluate(clean, 'clipping')
    assert result['pieces'] == [] and {row['code'] for row in result['excluded']} == {'OUTSIDE_OBSERVATION'}


def test_open_report_clipped_to_shift_end(dirty):
    row = next(row for row in evaluate(dirty, 'clipping')['pieces'] if row['id'] == 'E-104')
    assert row['end'] == instant('2026-11-20T04:00:00+08:00') and row['seconds'] == 3600


def test_cutoff_splits_observed_interval(clean):
    clean['cutoff'] = '2026-11-19T22:15:00+08:00'
    assert [row['seconds'] for row in evaluate(clean, 'clipping')['pieces']] == [900]


def test_split_shift_removes_gap(clean):
    clean['shifts'][:1] = [
        {'device': '001', 'day': '2026-11-19', 'from': '21:00:00', 'to': '22:15:00'},
        {'device': '001', 'day': '2026-11-19', 'from': '22:45:00', 'to': '02:00:00'},
    ]
    result = evaluate(clean, 'clipping')
    assert [row['seconds'] for row in result['pieces'] if row['device'] == '001'] == [900, 900]
    assert result['excluded'][0]['seconds'] == 1800


def test_calendar_clips_outer_window(clean):
    clean['start'] = '2026-11-19T22:20:00+08:00'
    row = evaluate(clean, 'clipping')['pieces'][0]
    assert row['seconds'] == 2400
