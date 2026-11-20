from app.intervals import intersect, span


def clip_events(events, devices, window):
    pieces, excluded = [], []
    for event in events:
        end = window.cutoff if event['end'] is None else min(event['end'], window.cutoff)
        observed = intersect(event['start'], end, window.start, window.end)
        if observed is None:
            excluded.append({'line': event['line'], 'id': event['id'], 'code': 'OUTSIDE_OBSERVATION'})
            continue
        parts = []
        for shift in devices[event['device']]['windows']:
            clipped = intersect(*observed, shift['start'], shift['end'])
            if clipped:
                parts.append({**event, 'reported_start': event['start'], **span(*clipped)})
        pieces.extend(parts)
        off_seconds = observed[1] - observed[0] - sum(part['seconds'] for part in parts)
        if off_seconds:
            excluded.append({'line': event['line'], 'id': event['id'], 'code': 'NON_SERVICE', 'seconds': off_seconds})
    return {'pieces': pieces, 'excluded': excluded}
