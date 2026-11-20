from app.contracts import issue, text
from app.reasons import REASONS
from app.times import instant


def permit_register(rows, devices):
    permits, isolated = [], []
    for line, raw in enumerate(rows, 1):
        try:
            device, permit_id, status = (text(raw, key) for key in ('device', 'id', 'status'))
            reason = raw.get('reason')
            if reason is not None and text(raw, 'reason') not in REASONS:
                raise ValueError('未知豁免原因')
            reason = reason.strip() if reason is not None else None
            start, end = instant(raw.get('start')), instant(raw.get('end'))
            if end <= start or status not in {'approved', 'pending', 'denied'}:
                raise ValueError('申请时段或状态无效')
        except (AttributeError, ValueError):
            isolated.append(issue(line, 'INVALID_PERMIT', raw))
            continue
        if device not in devices:
            isolated.append(issue(line, 'UNKNOWN_DEVICE', raw))
            continue
        if status == 'approved':
            try:
                text(raw, 'approval')
            except ValueError:
                isolated.append(issue(line, 'MISSING_APPROVAL', raw))
                continue
        permits.append({'device': device, 'id': permit_id, 'status': status, 'reason': reason,
                        'start': start, 'end': end, 'line': line, 'raw': raw})
    return permits, isolated
