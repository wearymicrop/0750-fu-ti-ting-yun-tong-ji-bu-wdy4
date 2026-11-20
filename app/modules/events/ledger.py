from collections import defaultdict

from app.contracts import issue, text
from app.reasons import REASONS
from app.times import instant


def parse_row(raw):
    device, event_id, reason = (text(raw, key) for key in ('device', 'id', 'reason'))
    start = instant(raw.get('start'))
    value = raw.get('end')
    end = instant(value) if value is not None else None
    if end is not None and end <= start:
        raise ValueError('恢复时刻必须晚于报码')
    return device, event_id, start, end, reason


def event_ledger(raw_rows, devices):
    groups = defaultdict(list)
    isolated, notices, events = [], [], []
    for line, raw in enumerate(raw_rows, 1):
        try:
            device, event_id, start, end, reason = parse_row(raw)
        except (ValueError, AttributeError):
            isolated.append(issue(line, 'INVALID_EVENT', raw))
            continue
        if device not in devices:
            isolated.append(issue(line, 'UNKNOWN_DEVICE', raw))
            continue
        groups[device, event_id].append({
            'device': device, 'id': event_id, 'start': start, 'end': end,
            'reason': reason, 'line': line, 'raw': raw,
        })

    conflicts, duplicates = 0, 0
    for group in groups.values():
        variants = {(row['start'], row['end'], row['reason']) for row in group}
        if len(variants) > 1:
            conflicts += len(group)
            for row in group:
                isolated.append(issue(row['line'], 'EVENT_CONFLICT', row['raw']))
                events.append({**row, 'lines': [row['line']], 'state': 'EVENT_CONFLICT'})
            continue
        first, *others = group
        duplicates += len(others)
        for row in others:
            notices.append({**issue(row['line'], 'DUPLICATE_EVENT', row['raw']), 'kept_line': first['line']})
        state = 'CONFIRMED'
        if first['reason'] not in REASONS:
            state = 'UNKNOWN_REASON'
        elif first['end'] is None:
            state = 'OPEN_EVENT'
        if state != 'CONFIRMED':
            notices.append(issue(first['line'], state, first['raw']))
        events.append({**first, 'lines': [row['line'] for row in group], 'state': state})

    accepted = len(events) - conflicts
    return {
        'events': sorted(events, key=lambda row: (row['device'], row['start'], row['line'])),
        'isolated': sorted(isolated, key=lambda row: row['line']),
        'notices': sorted(notices, key=lambda row: row['line']),
        'counts': {'input': len(raw_rows), 'accepted': accepted, 'isolated': len(isolated), 'duplicates': duplicates},
    }
