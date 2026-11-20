from app.modules.reconcile.balance import reconcile
from app.pipeline import evaluate


def test_clean_has_exact_measured_rate(clean):
    result = evaluate(clean, 'reconcile')
    assert result['status'] == 'MATCHED'
    assert result['totals'] == {'service': 28800, 'available': 23400, 'responsible': 3600, 'exempt': 1800,
                                'missing': 0, 'difference': 0, 'denominator': 27000,
                                'availability_bps': 8667, 'lower_bound_bps': 8667}


def test_dirty_has_lower_bound_only(dirty):
    result = evaluate(dirty, 'reconcile')
    assert result['status'] == 'MISSING_EVIDENCE'
    assert result['totals'] == {'service': 36000, 'available': 13500, 'responsible': 12600, 'exempt': 4500,
                                'missing': 5400, 'difference': 0, 'denominator': 31500,
                                'availability_bps': None, 'lower_bound_bps': 4286}


def test_per_device_conservation_and_contiguity(dirty):
    result = evaluate(dirty)
    for device, entry in result['schedules']['devices'].items():
        rows = [row for row in result['segments'] if row['device'] == device]
        window, = entry['windows']
        assert rows[0]['start'] == window['start'] and rows[-1]['end'] == window['end']
        assert all(left['end'] == right['start'] for left, right in zip(rows, rows[1:]))
        assert sum(row['seconds'] for row in rows) == result['reconcile']['by_device'][device]['service']


def test_by_cause_excludes_conflicts(dirty):
    totals = evaluate(dirty, 'reconcile')['by_cause']
    assert totals == {'SAFETY': {'responsible': 3600, 'exempt': 3600},
                      'POWER': {'responsible': 3600, 'exempt': 0},
                      'MECHANICAL': {'responsible': 2700, 'exempt': 0},
                      'MAINTENANCE': {'responsible': 2700, 'exempt': 900}}


def test_no_service_has_no_rate(clean):
    clean['shifts'] = []
    result = evaluate(clean, 'reconcile')
    assert result['status'] == 'NO_SERVICE'
    assert result['totals']['service'] == 0 and result['totals']['availability_bps'] is None


def test_all_exempt_has_no_denominator():
    result = reconcile({'A': {'windows': [{'seconds': 500}]}}, [
        {'device': 'A', 'bucket': 'exempt', 'seconds': 500, 'code': 'SAFETY'},
    ])
    assert result['totals']['denominator'] == 0 and result['totals']['lower_bound_bps'] is None


def test_mismatch_is_detected_even_when_net_delta_cancels():
    devices = {'A': {'windows': [{'seconds': 50}]}, 'B': {'windows': [{'seconds': 50}]}}
    result = reconcile(devices, [{'device': 'A', 'bucket': 'available', 'seconds': 100}])
    assert result['status'] == 'UNBALANCED' and result['totals']['difference'] == 0
    assert [result['by_device'][key]['difference'] for key in devices] == [-50, 50]
