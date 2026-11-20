import json
import sqlite3

from app.config import database_path
from app.errors import BusinessError
from app.modules.reports.manifest import canonical

_SCHEMA = '''CREATE TABLE IF NOT EXISTS openings (
    report_id TEXT PRIMARY KEY,
    batch_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)'''


def _connect():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    with connection:
        connection.execute(_SCHEMA)
    return connection


def save_opening(batch):
    connection = _connect()
    try:
        with connection:
            cursor = connection.execute(
                'INSERT INTO openings (report_id, batch_json) VALUES (?, ?) ON CONFLICT(report_id) DO NOTHING',
                (batch['report_id'], canonical(batch)))
        row = connection.execute('SELECT batch_json FROM openings WHERE report_id = ?',
                                 (batch['report_id'],)).fetchone()
        return {**json.loads(row[0]), 'reused': cursor.rowcount == 0}
    finally:
        connection.close()


def fetch_opening(report_id):
    connection = _connect()
    try:
        row = connection.execute('SELECT batch_json FROM openings WHERE report_id = ?',
                                 (report_id,)).fetchone()
    finally:
        connection.close()
    if row is None:
        raise BusinessError('OPENING_NOT_FOUND', '该班报尚未形成开放记录', 404)
    return json.loads(row[0])


def list_openings():
    connection = _connect()
    try:
        rows = connection.execute(
            'SELECT batch_json, created_at FROM openings ORDER BY created_at DESC, rowid DESC LIMIT 30').fetchall()
    finally:
        connection.close()
    batches = []
    for encoded, created in rows:
        batch = json.loads(encoded)
        batches.append({'report_id': batch['report_id'], 'summary': batch['summary'],
                        'rule_version': batch['rule_version'], 'created_at': created})
    return {'openings': batches}
