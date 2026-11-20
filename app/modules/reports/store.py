import json
import sqlite3
from contextlib import contextmanager

from app.config import database_path
from app.errors import BusinessError
from app.modules.reports.manifest import canonical

_SCHEMA = '''CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    input_json TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)'''


@contextmanager
def database():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    try:
        with connection:
            connection.execute(_SCHEMA)
            yield connection
    finally:
        connection.close()


def save(data, report):
    with database() as connection:
        cursor = connection.execute(
            'INSERT INTO reports (id, input_json, snapshot_json) VALUES (?, ?, ?) ON CONFLICT(id) DO NOTHING',
            (report['id'], canonical(data), canonical(report)),
        )
        row = connection.execute('SELECT snapshot_json FROM reports WHERE id = ?', (report['id'],)).fetchone()
        return {**json.loads(row[0]), 'reused': cursor.rowcount == 0}


def fetch(report_id):
    with database() as connection:
        row = connection.execute('SELECT input_json, snapshot_json FROM reports WHERE id = ?', (report_id,)).fetchone()
    if row is None:
        raise BusinessError('REPORT_NOT_FOUND', '班报不存在', 404)
    return tuple(json.loads(column) for column in row)


def history():
    with database() as connection:
        rows = connection.execute('SELECT snapshot_json, created_at FROM reports ORDER BY created_at DESC, rowid DESC LIMIT 30').fetchall()
    reports = []
    for encoded, created in rows:
        report = json.loads(encoded)
        reports.append({'id': report['id'], 'manifest': report['manifest'], 'created_at': created,
                        'status': report['result']['reconcile']['status']})
    return reports
