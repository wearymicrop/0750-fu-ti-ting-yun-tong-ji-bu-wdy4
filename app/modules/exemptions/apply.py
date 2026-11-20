from collections import defaultdict

from app.intervals import intersect, span


def apply_permits(segments, permits):
    registered = defaultdict(list)
    for permit in permits:
        if permit['status'] == 'approved':
            registered[permit['device']].append(permit)
    output = []
    for segment in segments:
        applied = []
        start, end = segment['start'], segment['end']
        if segment['bucket'] == 'responsible':
            for permit in registered[segment['device']]:
                if permit['reason'] not in (None, segment['code']):
                    continue
                common = intersect(start, end, permit['start'], permit['end'])
                if common:
                    applied.append((*common, permit['line']))
        boundaries = sorted({start, end, *(edge for lo, hi, _ in applied for edge in (lo, hi))})
        for lo, hi in zip(boundaries, boundaries[1:]):
            lines = sorted(line for left, right, line in applied if left <= lo < right)
            output.append({**segment, **span(lo, hi),
                           'bucket': 'exempt' if lines else segment['bucket'], 'permit_lines': lines})
    return output
