import {$, buckets, cards, label, num, rate, table} from './format.mjs';
import {drawTimeline} from './timeline.mjs';

export function drawOverview(result, showEvidence) {
  const {totals, by_device, status} = result.reconcile;
  const keys = Object.keys(buckets);
  cards($('kpis'), [
    ['营业时长', `${num(totals.service)} 秒`],
    ...keys.map(key => [buckets[key], `${num(totals[key])} 秒`, key]),
    totals.missing ? ['可用率下限', rate(totals.lower_bound_bps), 'accent']
      : ['确认可用率', rate(totals.availability_bps), 'accent'],
  ]);
  $('balance').textContent = label(status);
  $('evidence').textContent = '请选择时间片段';
  drawTimeline(result, showEvidence);
  table($('device-table'), [['设备'], ['营业', true], ...keys.map(key => [buckets[key], true]), ['差额', true], ['可用率', true]],
    Object.entries(by_device).map(([key, row]) => [
      `${key} · ${result.schedules.devices[key].name}`, num(row.service), ...keys.map(field => num(row[field])),
      num(row.difference), row.missing && row.lower_bound_bps != null ? `≥ ${rate(row.lower_bound_bps)}` : rate(row.availability_bps),
    ]));
}
