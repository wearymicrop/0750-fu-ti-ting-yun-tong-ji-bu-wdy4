from app.pipeline import evaluate


def test_timezone_equivalent_duplicate(dirty):
    # TRAP-11
    result = evaluate(dirty, 'events')
    east = next(row for row in result['events'] if row['id'] == 'E-101')
    assert east['lines'] == [2, 6]
    assert result['notices'][-1]['kept_line'] == 2


def test_conflicting_report_codes_quarantined(dirty):
    # TRAP-14
    result = evaluate(dirty, 'events')
    assert [row['line'] for row in result['isolated'] if row['code'] == 'EVENT_CONFLICT'] == [8, 9]
    assert len([row for row in result['events'] if row['state'] == 'EVENT_CONFLICT']) == 2


def test_out_of_order_records_retained(dirty):
    # TRAP-13
    result = evaluate(dirty, 'events')
    assert [row['line'] for row in result['events'] if row['device'] == '001'] == [2, 5, 4, 7, 3]


def test_null_close_marked_unknown(dirty):
    # TRAP-07
    result = evaluate(dirty, 'events')
    event = next(row for row in result['events'] if row['line'] == 3)
    assert event['end'] is None and event['state'] == 'OPEN_EVENT'


def test_event_counts_conserve(dirty):
    counts = evaluate(dirty, 'events')['counts']
    assert counts == {'input': 11, 'accepted': 6, 'isolated': 4, 'duplicates': 1}
    assert counts['input'] == counts['accepted'] + counts['isolated'] + counts['duplicates']


def test_invalid_and_off_register_rows_have_codes(dirty):
    result = evaluate(dirty, 'events')
    assert [(row['line'], row['code']) for row in result['isolated'][-2:]] == [(10, 'INVALID_EVENT'), (11, 'UNKNOWN_DEVICE')]


def test_code_is_scoped_to_one_device(clean):
    clean['events'][1]['id'] = clean['events'][0]['id']
    result = evaluate(clean, 'events')
    assert result['counts']['accepted'] == 2 and result['isolated'] == []


def test_unknown_reason_still_links_evidence(clean):
    clean['events'][0]['reason'] = 'OTHER'
    result = evaluate(clean, 'events')
    assert result['notices'] == [{'line': 1, 'code': 'UNKNOWN_REASON', 'raw': clean['events'][0]}]
