import os
from datetime import timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = timezone(timedelta(hours=8), 'Asia/Shanghai')
RULE_VERSION = '2026.11.1'


def database_path():
    return Path(os.environ.get('LIFT_DB', ROOT / 'instance' / 'reports.sqlite'))
