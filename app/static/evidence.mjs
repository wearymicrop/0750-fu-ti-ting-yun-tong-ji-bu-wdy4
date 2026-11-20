import {$, buckets, el, label, num} from './format.mjs';

function rows(title, data, toLine) {
  if (!data.length) return [];
  const list = el('ul', null, 'evidence-lines');
  for (const item of data) {
    const [primary, detail] = toLine(item);
    const entry = el('li', primary, item.winner ? 'winner' : '');
    if (detail) entry.append(el('small', detail));
    list.append(entry);
  }
  return [el('h3', title), list];
}

export function drawEvidence(data) {
  const {segment} = data;
  const period = el('p', null, 'evidence-window');
  period.append(`${data.start_local.slice(5, 19).replace('T', ' ')} → ${data.end_local.slice(5, 19).replace('T', ' ')}`);
  $('evidence').replaceChildren(
    period,
    el('p', `${segment.device} · ${buckets[segment.bucket]} · ${label(segment.code)} · ${num(segment.seconds)} 秒`),
    ...rows('事件行', data.events, item => [
      `${item.id} · 第 ${item.line} 行 · ${label(item.reason)}${item.winner ? ' · 归属' : ''}`,
      `${item.raw.start} → ${item.raw.end ?? '未恢复'}`,
    ]),
    ...rows('重传行', data.retransmissions, item => [`第 ${item.line} 行 → 第 ${item.kept_line} 行`, item.raw.start]),
    ...rows('豁免凭据', data.permits, item => [`${item.id} · 第 ${item.line} 行`, item.raw.approval]),
    ...rows('营业班表', data.shifts, item => [`第 ${item.line} 行 · ${item.raw.day}`, `${item.raw.from} → ${item.raw.to}`]),
  );
}
