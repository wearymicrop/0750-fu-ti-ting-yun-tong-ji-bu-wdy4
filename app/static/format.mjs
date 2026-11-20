export const buckets = {available: '可用', responsible: '责任停运', exempt: '豁免', missing: '缺证'};
const labels = {
  SAFETY: '安全联锁', POWER: '供电中断', MECHANICAL: '机械故障', MAINTENANCE: '计划检修',
  NO_STOP: '无停运记录', OPEN_EVENT: '未恢复报码', UNKNOWN_REASON: '原因缺证',
  AFTER_CUTOFF: '超出采信时刻', EVENT_CONFLICT: '报码冲突', DUPLICATE_EVENT: '重复报码',
  UNKNOWN_DEVICE: '设备不在册', INVALID_SHIFT: '班表格式有误', INVALID_DEVICE: '设备信息有误',
  CONFLICT_DEVICE: '设备号冲突', INVALID_EVENT: '事件时段有误', INVALID_PERMIT: '豁免时段或状态有误',
  MISSING_APPROVAL: '缺审批凭据', OUTSIDE_OBSERVATION: '超出采信窗口', NON_SERVICE: '非营业时段',
  MATCHED: '时长已对平', MISSING_EVIDENCE: '时长对平 · 有缺证', NO_SERVICE: '无营业时段',
  UNBALANCED: '时长有差额', CONFIRMED: '已确认', approved: '已批准', pending: '待审批', denied: '未批准',
  clean: '干净样例', dirty: '异常样例', custom: '本地班报',
};
export const label = value => labels[value] ?? value ?? '—';
export const num = value => value == null ? '—' : value.toLocaleString('zh-CN');
export const rate = value => value == null ? '—' : `${(value / 100).toFixed(2)}%`;
const time = new Intl.DateTimeFormat('zh-CN', {timeZone: 'Asia/Shanghai', hourCycle: 'h23', hour: '2-digit', minute: '2-digit'});
const full = new Intl.DateTimeFormat('zh-CN', {timeZone: 'Asia/Shanghai', hourCycle: 'h23', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'});
export const clock = seconds => time.format(seconds * 1000);
export const stamp = seconds => seconds == null ? '—' : full.format(seconds * 1000);
export const $ = id => document.getElementById(id);
export function el(tag, value, className) {
  const node = document.createElement(tag);
  if (value != null) node.textContent = value;
  if (className) node.className = className;
  return node;
}
export function cards(target, rows) {
  target.replaceChildren(...rows.map(([name, value, color]) => {
    const card = el('div', null, 'kpi');
    if (color) card.style.setProperty('--metric', `var(--${color})`);
    card.append(el('span', name), el('strong', value));
    return card;
  }));
}
export function table(target, columns, rows) {
  if (!rows.length) {
    target.replaceChildren(el('p', '暂无记录', 'empty'));
    return;
  }
  const grid = el('table');
  const header = grid.createTHead().insertRow();
  for (const [title, numeric] of columns) {
    const cell = el('th', title, numeric ? 'num' : '');
    cell.scope = 'col';
    header.append(cell);
  }
  const body = grid.createTBody();
  for (const row of rows) {
    const entry = body.insertRow();
    row.forEach((value, index) => {
      const cell = entry.insertCell();
      if (columns[index][1]) cell.className = 'num';
      cell.append(value instanceof Node ? value : String(value ?? '—'));
    });
  }
  target.replaceChildren(grid);
}
