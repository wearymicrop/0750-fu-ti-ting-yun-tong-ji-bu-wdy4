from app.errors import BusinessError
from app.times import local_time


def segment_evidence(result, device, start):
    row = next((item for item in result['segments'] if item['device'] == device and item['start'] == start), None)
    if row is None:
        raise BusinessError('SEGMENT_NOT_FOUND', '该设备时刻没有片段', 404)
    event_lines = set(row['event_lines'])
    events = []
    for event in result['events']['events']:
        if not event_lines.intersection(event['lines']):
            continue
        events.append({**event, 'winner': event['line'] == row['winner_line']})
    retransmissions = [item for item in result['events']['notices']
                       if item['code'] == 'DUPLICATE_EVENT' and item['line'] in event_lines]
    permits = [permit for permit in result['permits'] if permit['line'] in row['permit_lines']]
    shifts = [shift for shift in result['schedules']['devices'][device]['shifts']
              if shift['start'] < row['end'] and row['start'] < shift['end']]
    return {'segment': row, 'start_local': local_time(row['start']), 'end_local': local_time(row['end']),
            'events': events, 'retransmissions': retransmissions, 'permits': permits, 'shifts': shifts}
