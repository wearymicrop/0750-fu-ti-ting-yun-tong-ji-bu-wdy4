import {$, cards, el, num, openingLabels, table} from './format.mjs';
import {request} from './api.mjs';

function verdictTag(status) {
  const node = el('span', openingLabels[status] ?? status, `verdict verdict-${status.toLowerCase()}`);
  return node;
}

function evidenceRows(findings) {
  if (!findings.length) return [el('p', '证据完整，无疑点', 'empty')];
  const list = el('ul', null, 'evidence-lines');
  for (const finding of findings) {
    const entry = el('li', null, `finding severity-${finding.severity.toLowerCase()}`);
    entry.append(
      el('strong', `${openingLabels[finding.code] ?? finding.code} · ${finding.severity === 'SUSPEND' ? '暂停' : '待复核'}`),
      el('small', `依据行 ${finding.lines.join('、') || '—'} · ${finding.detail}`),
    );
    list.append(entry);
  }
  return list;
}

export function drawOpening(batch) {
  cards($('opening-kpis'), [
    ['开放', num(batch.summary.OPEN), 'available'],
    ['暂停', num(batch.summary.SUSPEND), 'responsible'],
    ['待复核', num(batch.summary.REVIEW), 'missing'],
    ['设备合计', num(batch.devices.length)],
  ]);
  const rows = batch.devices.map(device => [
    `${device.device} · ${device.name}`, verdictTag(device.status),
    num(device.finding_count), evidenceRows(device.findings),
  ]);
  table($('opening-table'), [['设备'], ['结论'], ['疑点', true], ['裁决依据']], rows);
}

export function resetOpening(hasReport) {
  $('opening-kpis').replaceChildren();
  $('opening-table').replaceChildren(
    el('p', hasReport ? '该班报尚未形成开放结论，点击右侧「形成开放结论」' : '请先在「班报归档」保存班报，再形成开放结论', 'empty'));
  $('opening-actions').hidden = !hasReport;
  $('opening-feedback').textContent = '';
}

export async function drawOpeningBatches(open) {
  const {openings} = await request('/api/openings');
  table($('opening-batch-table'), [['班报'], ['开放/暂停/复核'], ['规则']], openings.map(item => {
    const link = el('button', item.report_id.slice(0, 12), 'mono');
    link.type = 'button';
    link.addEventListener('click', () => open(item.report_id));
    const counts = `${item.summary.OPEN}/${item.summary.SUSPEND}/${item.summary.REVIEW}`;
    return [link, counts, item.rule_version];
  }));
  return openings;
}

export function wireOpening({getReport, onBatch}) {
  const feedback = $('opening-feedback');
  $('opening-form').addEventListener('click', async () => {
    const report = getReport();
    if (!report) {
      feedback.textContent = '请先保存或打开一份班报';
      return;
    }
    $('opening-form').disabled = true;
    try {
      const batch = await request(`/api/runs/${report.id}/openings`, {});
      feedback.textContent = batch.reused ? '该班报开放结论已存在，按留档复用' : '开放结论已形成并留档';
      await onBatch(report.id);
    } catch (error) {
      feedback.textContent = error.message;
    } finally {
      $('opening-form').disabled = false;
    }
  });
}

export function setOpeningActions(batch) {
  $('opening-actions').hidden = !batch;
  if (batch) $('opening-download').href = `/api/runs/${batch.report_id}/openings/export`;
}
