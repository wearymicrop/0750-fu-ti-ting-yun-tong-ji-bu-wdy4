def intersect(start, end, left, right):
    lo, hi = max(start, left), min(end, right)
    return (lo, hi) if lo < hi else None


def merge(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def span(start, end):
    return {'start': start, 'end': end, 'seconds': end - start}
