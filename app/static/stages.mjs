import {$, buckets, cards, label, num, stamp, table} from './format.mjs';

function sheet(title, columns, rows) {
  return {title, columns, rows};
}
const issues = rows => sheet('诊断记录', [['行号', true], ['原因'], ['来源']], rows.map(row => [
  row.line, label(row.code), row.raw?.id ?? row.raw?.device ?? row.id ?? '—',
]));
const segments = rows => rows.map(row => [row.device, stamp(row.start), stamp(row.end), buckets[row.bucket], label(row.code), row.winner_line, num(row.seconds)]);
const segmentColumns = [['设备'], ['开始'], ['结束'], ['状态'], ['原因'], ['归属行', true], ['秒数', true]];
const views = {
  schedules(result) {
    const {devices, device_issues, shift_issues} = result.schedules;
    const rows = Object.entries(devices).flatMap(([key, device]) => device.windows.map(window => [key, device.name, stamp(window.start), stamp(window.end), num(window.seconds)]));
    return [sheet('合并班表', [['设备'], ['名称'], ['开始'], ['结束'], ['秒数', true]], rows), issues([...device_issues, ...shift_issues])];
  },
  events(result) {
    const {events, isolated, notices} = result.events;
    return [sheet('报码台账', [['行号', true], ['设备'], ['报码'], ['发生'], ['恢复'], ['状态']], events.map(row => [row.line, row.device, row.id, stamp(row.start), stamp(row.end), label(row.state)])), issues([...isolated, ...notices])];
  },
  clipping(result) {
    const {pieces, excluded} = result.clipping;
    return [sheet('营业内片段', [['设备'], ['报码'], ['开始'], ['结束'], ['秒数', true]], pieces.map(row => [row.device, row.id, stamp(row.start), stamp(row.end), num(row.seconds)])),
      sheet('裁切记录', [['行号', true], ['报码'], ['原因'], ['秒数', true]], excluded.map(row => [row.line, row.id, label(row.code), num(row.seconds)]))];
  },
  attribution(result) {
    return [sheet('优先级分段', segmentColumns, segments(result.attributed)),
      sheet('原因时长', [['原因'], ['责任秒数', true], ['豁免秒数', true]], Object.entries(result.reconcile.by_cause).map(([code, row]) => [label(code), num(row.responsible), num(row.exempt)]))];
  },
  exemptions(result) {
    const approved = result.segments.filter(row => row.bucket === 'exempt');
    return [sheet('实际豁免', [...segmentColumns, ['审批行']], segments(approved).map((row, index) => [...row, approved[index].permit_lines.join('、')])),
      sheet('审批记录', [['行号', true], ['凭据'], ['状态']], [...result.permits.map(row => [row.line, row.id, label(row.status)]), ...result.permit_issues.map(row => [row.line, row.raw?.id, label(row.code)])])];
  },
};

export function drawStage(key, result) {
  const [main, side] = views[key](result);
  $('stage-title').textContent = main.title;
  $('stage-side-title').textContent = side.title;
  cards($('stage-kpis'), [[main.title, num(main.rows.length)], [side.title, num(side.rows.length)]]);
  table($('stage-data'), main.columns, main.rows);
  table($('stage-side'), side.columns, side.rows);
}
