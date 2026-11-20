import {$, stamp} from './format.mjs';
import {request} from './api.mjs';
import {drawOverview} from './reconcile.mjs';
import {drawEvidence} from './evidence.mjs';
import {drawStage} from './stages.mjs';
import {drawArchive, drawArchived} from './archive.mjs';
import {drawOpening, drawOpeningBatches, resetOpening, setOpeningActions, wireOpening} from './openings.mjs';

const links = [...document.querySelectorAll('[data-section]')];
const state = {sample: 'dirty', result: null, report: null, evidenceKey: 0, opening: null};
const status = value => { $('status').textContent = value; };

async function inspect(segment) {
  const key = ++state.evidenceKey;
  const source = state.report && state.report.result === state.result ? `/api/runs/${state.report.id}` : `/api/preview/${state.sample}`;
  const args = new URLSearchParams({device: segment.device, start: segment.start});
  try {
    const data = await request(`${source}/evidence?${args}`);
    if (key === state.evidenceKey) drawEvidence(data);
  } catch (error) {
    if (key === state.evidenceKey) $('evidence').textContent = error.message;
  }
}

function syncView() {
  const active = links.find(link => link.dataset.section === window.location.hash.slice(1)) ?? links[0];
  const section = active.dataset.section;
  for (const link of links) {
    if (link === active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  $('page-title').textContent = active.textContent.trim();
  $('overview').hidden = section !== 'reconcile';
  $('archive').hidden = section !== 'runs';
  $('openings').hidden = section !== 'openings';
  $('stage').hidden = ['reconcile', 'runs', 'openings'].includes(section);
  if (section === 'runs') {
    drawArchived(state.report);
    drawArchive(openReport).catch(error => status(error.message));
  } else if (section === 'openings') {
    showOpenings();
  } else if (state.result) {
    if (section === 'reconcile') drawOverview(state.result, inspect);
    else drawStage(section, state.result);
  }
}

async function openBatch(reportId) {
  try {
    state.opening = await request(`/api/runs/${reportId}/openings`);
    drawOpening(state.opening);
    setOpeningActions(state.opening);
    $('opening-feedback').textContent = '已读取留档开放记录';
  } catch (error) {
    $('opening-feedback').textContent = error.message;
  }
}

async function showOpenings() {
  try {
    const batches = await drawOpeningBatches(openBatch);
    const current = state.report && batches.find(item => item.report_id === state.report.id);
    if (current) {
      await openBatch(current.report_id);
      return;
    }
    state.opening = null;
    $('opening-actions').hidden = !state.report;
    resetOpening(Boolean(state.report));
  } catch (error) { status(error.message); }
}

function showResult(result) {
  state.evidenceKey++;
  state.result = result;
  $('range').textContent = `${stamp(result.window.start)} → ${stamp(result.window.end)}`;
  syncView();
}

let loadKey = 0;
async function loadSample() {
  const key = ++loadKey;
  const sample = $('sample').value;
  status('载入中');
  $('save').disabled = true;
  try {
    const result = await request(`/api/preview/${sample}`);
    if (key !== loadKey) return;
    state.sample = sample;
    state.report = null;
    showResult(result);
    status('样例已计算');
  } catch (error) {
    if (key === loadKey) {
      $('sample').value = state.sample;
      status(error.message);
    }
  } finally {
    if (key === loadKey) $('save').disabled = !state.result;
  }
}

async function saveReport(body) {
  const report = await request('/api/runs', body);
  state.report = report;
  showResult(report.result);
  status(report.reused ? '已复用同一班报' : '班报已保存');
}

async function openReport(id) {
  try {
    state.report = await request(`/api/runs/${id}`);
    state.sample = state.report.manifest.source;
    $('sample').value = state.sample;
    $('run-feedback').textContent = '';
    showResult(state.report.result);
    status('已读取归档');
  } catch (error) { status(error.message); }
}

$('sample').addEventListener('change', loadSample);
window.addEventListener('hashchange', syncView);
$('save').addEventListener('click', async () => {
  if (state.sample === 'custom' && state.report) {
    window.location.hash = 'runs';
    return;
  }
  $('save').disabled = true;
  $('sample').disabled = true;
  $('upload-button').disabled = true;
  try {
    await saveReport({sample: state.sample});
    window.location.hash = 'runs';
  } catch (error) { status(error.message); }
  finally {
    $('save').disabled = false;
    $('sample').disabled = false;
    $('upload-button').disabled = false;
  }
});
$('upload-button').addEventListener('click', () => $('upload').click());
$('upload').addEventListener('change', async () => {
  const file = $('upload').files[0];
  if (!file) return;
  $('sample').disabled = true;
  $('save').disabled = true;
  $('upload-button').disabled = true;
  try {
    if (file.size > 2_000_000) throw new Error('文件须小于 2 MB');
    const data = JSON.parse(await file.text());
    loadKey++;
    await saveReport({data});
    state.sample = 'custom';
    $('sample').value = 'custom';
    window.location.hash = 'reconcile';
  } catch (error) {
    status(error instanceof SyntaxError ? 'JSON 格式有误，请修正后重选' : error.message);
  } finally {
    $('upload').value = '';
    $('sample').disabled = false;
    $('save').disabled = !state.result;
    $('upload-button').disabled = false;
  }
});
$('rerun').addEventListener('click', async () => {
  if (!state.report) return;
  $('rerun').disabled = true;
  try {
    await request(`/api/runs/${state.report.id}/rerun`, {});
    $('run-feedback').textContent = '重跑一致';
  } catch (error) { $('run-feedback').textContent = error.message; }
  finally { $('rerun').disabled = false; }
});
$('save').disabled = true;
wireOpening({
  getReport: () => state.report,
  onBatch: async reportId => {
    await showOpenings();
    await openBatch(reportId);
  },
});
syncView();
loadSample();
