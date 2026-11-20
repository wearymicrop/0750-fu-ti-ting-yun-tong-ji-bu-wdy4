from app.config import RULE_VERSION
from app.modules.openings.verdict import adjudicate
from app.modules.reports.manifest import canonical, sha256


def build_opening(snapshot):
    result = snapshot['result']
    verdict = adjudicate(result)
    record = {
        'rule_version': RULE_VERSION,
        'window': result['window'],
        'summary': verdict['summary'],
        'statuses': verdict['statuses'],
        'devices': verdict['devices'],
    }
    digest = sha256({'verdict': record, 'input_sha256': snapshot['manifest']['input_sha256']})
    return {
        'report_id': snapshot['id'],
        'manifest': {
            'source': snapshot['manifest']['source'],
            'rule_version': RULE_VERSION,
            'input_sha256': snapshot['manifest']['input_sha256'],
            'result_digest': snapshot['manifest']['digest'],
            'digest': digest,
        },
        **record,
    }


def opening_payload(batch, data):
    """下载附件：开放结论 + 留档原始输入，与页面展示同源。"""
    return canonical({'batch': batch, 'input': data}) + '\n'
