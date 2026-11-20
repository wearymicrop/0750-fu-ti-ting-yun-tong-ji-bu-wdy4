import {$, el, label, table} from './format.mjs';
import {request} from './api.mjs';

export function drawArchived(report) {
  $('archive-actions').hidden = !report;
  $('archive-detail').replaceChildren();
  if (!report) return;
  $('download').href = `/api/runs/${report.id}/export`;
  for (const [key, value] of [['班报', report.id], ['规则', report.manifest.rule_version], ['摘要', report.manifest.digest]]) {
    $('archive-detail').append(el('dt', key), el('dd', value, 'mono'));
  }
}

export async function drawArchive(open) {
  const {runs} = await request('/api/runs');
  table($('archive-table'), [['班报'], ['来源'], ['对账状态']], runs.map(run => {
    const link = el('button', run.id.slice(0, 12), 'mono');
    link.type = 'button';
    link.addEventListener('click', () => open(run.id));
    return [link, label(run.manifest.source), label(run.status)];
  }));
}
