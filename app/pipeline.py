from dataclasses import asdict

from app.contracts import parse_batch
from app.modules.attribution.sweep import attribute
from app.modules.clipping.cut import clip_events
from app.modules.events.ledger import event_ledger
from app.modules.exemptions.apply import apply_permits
from app.modules.exemptions.register import permit_register
from app.modules.reconcile.balance import reconcile
from app.modules.schedules.calendar import build_calendar
from app.samples import load_sample


def evaluate(data, stop=None):
    window = parse_batch(data)
    calendar = build_calendar(data, window)
    if stop == 'schedules':
        return {'window': asdict(window), **calendar}
    devices = calendar['devices']
    ledger = event_ledger(data['events'], devices)
    if stop == 'events':
        return ledger
    cuts = clip_events(ledger['events'], devices, window)
    if stop == 'clipping':
        return cuts
    attributed = attribute(devices, cuts['pieces'], window.cutoff)
    if stop == 'attribution':
        return {'segments': attributed}
    permits, isolated = permit_register(data['permits'], devices)
    final = apply_permits(attributed, permits)
    exemptions = {'permits': permits, 'isolated': isolated, 'segments': final}
    if stop == 'exemptions':
        return exemptions
    balance = reconcile(devices, final)
    if stop == 'reconcile':
        return balance
    return {
        'window': asdict(window), 'schedules': calendar, 'events': ledger, 'clipping': cuts,
        'attributed': attributed, 'permits': permits, 'permit_issues': isolated, 'segments': final, 'reconcile': balance,
    }


def sample_stage(sample, stage):
    return evaluate(load_sample(sample), stage)
