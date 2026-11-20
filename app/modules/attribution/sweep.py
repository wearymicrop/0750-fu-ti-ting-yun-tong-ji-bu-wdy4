from collections import defaultdict
from heapq import heappop, heappush

from app.intervals import span
from app.reasons import REASONS


def rank(event):
    priority = REASONS[event['reason']][0] if event['state'] == 'CONFIRMED' else 100
    return priority, event['reported_start'], event['id'], event['line']


def divide(window, pieces, cutoff):
    starts, ends = defaultdict(list), defaultdict(list)
    for index, event in enumerate(pieces):
        starts[event['start']].append(index)
        ends[event['end']].append(index)
    boundaries = {window['start'], window['end'], *starts, *ends}
    if window['start'] < cutoff < window['end']:
        boundaries.add(cutoff)
    ordered = sorted(boundaries)
    active, heap = set(), []
    for start, end in zip(ordered, ordered[1:]):
        active.difference_update(ends[start])
        for index in starts[start]:
            active.add(index)
            heappush(heap, (rank(pieces[index]), index))
        while heap and heap[0][1] not in active:
            heappop(heap)
        event = pieces[heap[0][1]] if heap else None
        if start >= cutoff:
            bucket, code = 'missing', 'AFTER_CUTOFF'
        elif event is None:
            bucket, code = 'available', 'NO_STOP'
        elif event['state'] == 'CONFIRMED':
            bucket, code = 'responsible', event['reason']
        else:
            bucket, code = 'missing', event['state']
        yield {
            **span(start, end), 'bucket': bucket, 'code': code,
            'winner_line': event['line'] if event else None,
            'event_lines': sorted({line for index in active for line in pieces[index]['lines']}),
        }


def attribute(devices, pieces, cutoff):
    by_device = defaultdict(list)
    for part in pieces:
        by_device[part['device']].append(part)
    segments = []
    for device, details in sorted(devices.items()):
        parts = by_device[device]
        cursor = 0
        ordered = sorted(parts, key=lambda row: row['start'])
        for window in details['windows']:
            first = cursor
            while cursor < len(ordered) and ordered[cursor]['start'] < window['end']:
                cursor += 1
            segments.extend({'device': device, **segment} for segment in divide(window, ordered[first:cursor], cutoff))
    return segments
