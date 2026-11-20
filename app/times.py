import re
from datetime import datetime

from app.config import LOCAL

_INSTANT = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)\Z')


def instant(value):
    if not isinstance(value, str) or not _INSTANT.fullmatch(value):
        raise ValueError('时间须带时区偏移及整秒')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if not 2000 <= parsed.year <= 2099:
        raise ValueError('年份须在 2000 至 2099')
    return int(parsed.timestamp())


def local_time(value):
    return datetime.fromtimestamp(value, LOCAL).isoformat(timespec='seconds')
