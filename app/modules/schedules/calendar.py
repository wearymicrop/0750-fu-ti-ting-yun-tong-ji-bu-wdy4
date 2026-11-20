import re
from datetime import date, datetime, time, timedelta

from app.config import LOCAL
from app.contracts import issue, text
from app.intervals import intersect, merge, span

_CLOCK = re.compile(r'(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d\Z')
_DAY = re.compile(r'\d{4}-\d{2}-\d{2}\Z')


def shift_span(row):
    day, start, end = (text(row, key) for key in ('day', 'from', 'to'))
    if not _DAY.fullmatch(day) or not 2000 <= int(day[:4]) <= 2099:
        raise ValueError('无效班次日期')
    if not _CLOCK.fullmatch(start) or not _CLOCK.fullmatch(end) or start == end:
        raise ValueError('无效班次时刻')
    day = date.fromisoformat(day)
    until = day + timedelta(days=end < start)
    return tuple(int(datetime.combine(day, clock, LOCAL).timestamp()) for day, clock in (
        (day, time.fromisoformat(start)), (until, time.fromisoformat(end)),
    ))


def build_calendar(data, window):
    devices, device_issues, rejected = {}, [], set()
    for line, row in enumerate(data['devices'], 1):
        try:
            key, name = text(row, 'device'), text(row, 'name')
        except (ValueError, AttributeError):
            device_issues.append(issue(line, 'INVALID_DEVICE', row))
            continue
        if key in devices or key in rejected:
            previous = devices.pop(key, None)
            if previous:
                device_issues.append(issue(previous['line'], 'CONFLICT_DEVICE', previous['raw']))
            device_issues.append(issue(line, 'CONFLICT_DEVICE', row))
            rejected.add(key)
        else:
            devices[key] = {'name': name, 'line': line, 'raw': row, 'shifts': []}

    shift_issues = []
    for line, row in enumerate(data['shifts'], 1):
        try:
            key = text(row, 'device')
            start, end = shift_span(row)
        except (ValueError, AttributeError):
            shift_issues.append(issue(line, 'INVALID_SHIFT', row))
            continue
        if key not in devices:
            shift_issues.append(issue(line, 'UNKNOWN_DEVICE', row))
            continue
        clipped = intersect(start, end, window.start, window.end)
        devices[key]['shifts'].append({'line': line, 'raw': row, **span(start, end), 'in_window': clipped})

    for device in devices.values():
        intervals = [row['in_window'] for row in device['shifts'] if row['in_window']]
        device['windows'] = [span(*interval) for interval in merge(intervals)]
    return {'devices': devices, 'device_issues': device_issues, 'shift_issues': shift_issues}
