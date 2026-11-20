from collections import defaultdict

BUCKETS = ('available', 'responsible', 'exempt', 'missing')


def metrics(service, counts):
    difference = service - sum(counts.values())
    denominator = service - counts['exempt']
    lower = ((counts['available'] * 10000 + denominator // 2) // denominator
             if denominator > 0 and difference == 0 else None)
    return {'service': service, **counts, 'difference': difference, 'denominator': denominator,
            'availability_bps': lower if counts['missing'] == 0 else None, 'lower_bound_bps': lower}


def reconcile(devices, segments):
    counts = defaultdict(lambda: dict.fromkeys(BUCKETS, 0))
    by_cause = defaultdict(lambda: {'responsible': 0, 'exempt': 0})
    for segment in segments:
        counts[segment['device']][segment['bucket']] += segment['seconds']
        if segment['bucket'] in ('responsible', 'exempt'):
            by_cause[segment['code']][segment['bucket']] += segment['seconds']
    by_device = {}
    for key, device in sorted(devices.items()):
        service = sum(shift['seconds'] for shift in device['windows'])
        by_device[key] = metrics(service, counts[key])
    totals = metrics(sum(row['service'] for row in by_device.values()), {
        key: sum(row[key] for row in by_device.values()) for key in BUCKETS
    })
    if any(row['difference'] for row in by_device.values()):
        status = 'UNBALANCED'
    elif not totals['service']:
        status = 'NO_SERVICE'
    elif totals['missing']:
        status = 'MISSING_EVIDENCE'
    else:
        status = 'MATCHED'
    return {'status': status, 'totals': totals, 'by_device': by_device, 'by_cause': dict(by_cause)}
