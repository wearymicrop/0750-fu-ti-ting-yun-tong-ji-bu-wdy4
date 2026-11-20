from app.pipeline import evaluate
from app.times import instant


def at(data, device, value):
    moment = instant(value)
    return next(row for row in evaluate(data, 'attribution')['segments'] if row['device'] == device and row['start'] <= moment < row['end'])


def test_higher_priority_wins_without_erasing_loser(dirty):
    # TRAP-19
    row = at(dirty, '001', '2026-11-19T21:45:00+08:00')
    assert (row['code'], row['winner_line'], row['event_lines']) == ('SAFETY', 5, [2, 5, 6])


def test_touching_events_do_not_compete(dirty):
    row = at(dirty, '001', '2026-11-19T23:30:00+08:00')
    assert row['event_lines'] == [4] and row['code'] == 'POWER'


def test_loser_resumes_after_winner_ends(dirty):
    row = at(dirty, '001', '2026-11-20T00:30:00+08:00')
    assert row['event_lines'] == [7] and row['code'] == 'MECHANICAL'


def test_priority_is_independent_of_input_order(dirty):
    prior = at(dirty, '001', '2026-11-19T21:40:00+08:00')
    dirty['events'].reverse()
    later = at(dirty, '001', '2026-11-19T21:40:00+08:00')
    assert prior['code'] == later['code'] == 'SAFETY' and prior['seconds'] == later['seconds'] == 1800


def test_same_priority_uses_original_start_even_when_clipped(clean):
    first = clean['events'][0]
    clean['events'] = [
        {**first, 'id': 'Z', 'start': '2026-11-19T20:15:00+08:00'},
        {**first, 'id': 'A', 'start': '2026-11-19T20:30:00+08:00'},
    ]
    row = at(clean, '001', '2026-11-19T21:30:00+08:00')
    assert row['winner_line'] == 1 and row['event_lines'] == [1, 2]


def test_unobserved_future_means_missing(clean):
    clean['cutoff'] = '2026-11-19T23:00:00+08:00'
    row = at(clean, '001', '2026-11-19T23:00:00+08:00')
    assert row['code'] == 'AFTER_CUTOFF' and row['seconds'] == 10800


def test_conflict_union_has_one_bucket(dirty):
    rows = evaluate(dirty, 'attribution')['segments']
    conflicts = [row for row in rows if row['code'] == 'EVENT_CONFLICT']
    assert [row['event_lines'] for row in conflicts] == [[9], [8, 9], [8]]
    assert sum(row['seconds'] for row in conflicts) == 1800


def test_confirmed_outage_wins_over_open_event(dirty):
    dirty['events'][2]['start'] = '2026-11-19T22:05:00+08:00'
    row = at(dirty, '001', '2026-11-19T22:10:00+08:00')
    assert (row['winner_line'], row['event_lines'], row['bucket']) == (5, [3, 5], 'responsible')
