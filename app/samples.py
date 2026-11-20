import json

from app.config import ROOT
from app.contracts import COLLECTIONS
from app.errors import BusinessError


def load_sample(name):
    if name not in {'clean', 'dirty'}:
        raise BusinessError('SAMPLE_NOT_FOUND', '样例不存在', 404)
    folder = ROOT / 'sample_data' / name
    data = json.loads((folder / 'window.json').read_text(encoding='utf-8'))
    for field in COLLECTIONS:
        data[field] = json.loads((folder / f'{field}.json').read_text(encoding='utf-8'))
    return data
