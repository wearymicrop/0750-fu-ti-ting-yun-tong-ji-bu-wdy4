from dataclasses import dataclass

from app.errors import BusinessError
from app.times import instant

COLLECTIONS = {'devices': 50, 'shifts': 500, 'events': 1000, 'permits': 500}


@dataclass(frozen=True)
class Window:
    start: int
    end: int
    cutoff: int


def parse_batch(data):
    try:
        window = Window(*(instant(data[key]) for key in ('start', 'end', 'cutoff')))
    except (KeyError, ValueError, TypeError) as error:
        raise BusinessError('INVALID_WINDOW', '请填写带时区的起止及采信时刻') from error
    if not 0 < window.end - window.start <= 7 * 86400 or not window.start <= window.cutoff <= window.end:
        raise BusinessError('INVALID_WINDOW', '统计窗口限七天，采信时刻须在窗口内')
    for field, limit in COLLECTIONS.items():
        rows = data.get(field)
        if not isinstance(rows, list) or len(rows) > limit:
            raise BusinessError('INVALID_ROWS', f'{field} 须为数组且最多 {limit} 行')
    return window


def text(row, key):
    value = row.get(key)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 120:
        raise ValueError(f'{key} 须为 1 至 120 字符的文本')
    return value.strip()


def issue(line, code, raw):
    return {'line': line, 'code': code, 'raw': raw}
