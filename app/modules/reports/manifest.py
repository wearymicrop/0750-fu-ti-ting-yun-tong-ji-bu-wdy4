import hashlib
import json
from time import perf_counter_ns

from app.config import RULE_VERSION
from app.pipeline import evaluate


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha256(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def build_report(source, data):
    started = perf_counter_ns()
    result = evaluate(data)
    input_digest = sha256(data)
    identity = sha256({'input': input_digest, 'rules': RULE_VERSION, 'source': source})
    return {
        'id': identity,
        'manifest': {
            'source': source, 'input_sha256': input_digest, 'rule_version': RULE_VERSION,
            'digest': sha256(result), 'duration_ms': (perf_counter_ns() - started) // 1_000_000,
            'parameters': result['window'],
        },
        'result': result,
    }
