from app.intervals import intersect
from app.times import instant, local_time

# 裁决等级：数值越小越严重，逐台取最严重的疑点定结论
SEVERITY = {'SUSPEND': 1, 'REVIEW': 2}
STATUSES = ('OPEN', 'SUSPEND', 'REVIEW')


def _window_intervals(device):
    return [(window['start'], window['end']) for window in device['windows']]


def _hits_service(device, start, end):
    return any(intersect(start, end, lo, hi) for lo, hi in _window_intervals(device))


def _finding(code, severity, lines, detail, raw):
    return {'code': code, 'severity': severity, 'lines': sorted(set(lines)),
            'detail': detail, 'raw': raw}


def _missing_findings(device_id, segments):
    findings = []
    for segment in segments:
        if segment['device'] != device_id or segment['bucket'] != 'missing':
            continue
        lines = segment['event_lines']
        if segment['code'] == 'OPEN_EVENT':
            code, severity = 'OPEN_OUTAGE', 'SUSPEND'
            detail = (f"报码在 {local_time(segment['end'])} 仍未恢复，"
                      f"营业内 {segment['seconds']} 秒停运无恢复凭据")
        else:
            code, severity = 'MISSING_EVIDENCE', 'REVIEW'
            detail = (f"{local_time(segment['start'])} 至 {local_time(segment['end'])} "
                      f"{segment['seconds']} 秒缺证（{segment['code']}）")
        findings.append(_finding(code, severity, lines, detail,
                                 {'start': segment['start'], 'end': segment['end'],
                                  'winner_line': segment['winner_line'], 'reason': segment['code']}))
    return findings


def _conflict_findings(device_id, result):
    findings = []
    device = result['schedules']['devices'][device_id]
    groups = {}
    for row in result['events']['events']:
        if row['device'] != device_id or row['state'] != 'EVENT_CONFLICT':
            continue
        end = result['window']['cutoff'] if row['end'] is None else row['end']
        if not _hits_service(device, row['start'], end):
            continue
        groups.setdefault(row['id'], {'lines': [], 'raws': []})
        groups[row['id']]['lines'].extend(row['lines'])
        groups[row['id']]['raws'].append(row['raw'])
    for event_id, group in sorted(groups.items()):
        findings.append(_finding(
            'REPORT_CONFLICT', 'REVIEW', group['lines'],
            f"同报码 {event_id} 存在 {len(group['lines'])} 份冲突载荷，争议时段无法定因",
            group['raws']))
    return findings


def _permit_findings(device_id, result):
    findings = []
    device = result['schedules']['devices'][device_id]
    for permit in result['permits']:
        if permit['device'] != device_id:
            continue
        if not _hits_service(device, permit['start'], permit['end']):
            continue
        if permit['reason'] == 'MAINTENANCE' and permit['status'] in ('pending', 'denied'):
            findings.append(_finding(
                'MAINTENANCE_UNAPPROVED', 'SUSPEND', [permit['line']],
                f"计划检修审批 {permit['id']} 状态为 {permit['status']}，未获批准不得放行", permit['raw']))
    for issue in result['permit_issues']:
        if issue['code'] != 'MISSING_APPROVAL' or issue['raw'].get('device') != device_id:
            continue
        try:
            start, end = issue['raw']['start'], issue['raw']['end']
        except (AttributeError, TypeError, KeyError):
            continue
        try:
            if not _hits_service(device, instant(start), instant(end)):
                continue
        except ValueError:
            continue
        findings.append(_finding(
            'APPROVAL_GAP', 'REVIEW', [issue['line']],
            f"审批 {issue['raw'].get('id', '—')} 标记已批准但缺少批准凭据，须人工补证", issue['raw']))
    return findings


def adjudicate(result):
    """逐台裁决开放结论。纯函数：同一 result 必产生同一结论。"""
    devices = []
    for device_id, device in sorted(result['schedules']['devices'].items()):
        findings = []
        if not device['windows']:
            findings.append(_finding(
                'NO_SERVICE', 'REVIEW', [device['line']],
                '该设备在统计窗口内没有有效营业班表，无法确认首班可开放', device['raw']))
        findings.extend(_missing_findings(device_id, result['segments']))
        findings.extend(_conflict_findings(device_id, result))
        findings.extend(_permit_findings(device_id, result))
        findings.sort(key=lambda item: (SEVERITY[item['severity']], item['code'],
                                        item['lines'][0] if item['lines'] else 0))
        status = 'OPEN'
        if findings:
            status = min((item['severity'] for item in findings), key=lambda name: SEVERITY[name])
        devices.append({
            'device': device_id, 'name': device['name'], 'status': status,
            'finding_count': len(findings), 'findings': findings,
        })
    summary = {key: sum(1 for row in devices if row['status'] == key) for key in STATUSES}
    return {'statuses': STATUSES, 'summary': summary, 'devices': devices}
