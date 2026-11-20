import {$, buckets, clock, el, label, stamp} from './format.mjs';

export function drawTimeline(result, onSegment) {
  const {window, segments} = result;
  const devices = Object.entries(result.schedules.devices).sort(([a], [b]) => a.localeCompare(b));
  const axis = el('div', null, 'axis');
  const grid = el('div', null, 'track-grid');
  const duration = window.end - window.start;
  for (let tick = 0; tick <= 5; tick++) {
    const point = el('span', clock(window.start + duration * tick / 5));
    point.style.left = `${tick * 20}%`;
    axis.append(point);
  }
  grid.append(el('span', '设备', 'eyebrow'), axis);
  const groups = new Map(devices.map(([key]) => [key, []]));
  for (const segment of segments) groups.get(segment.device).push(segment);
  for (const [key, device] of devices) {
    const name = el('div', device.name, 'lane-label');
    name.append(el('small', key, 'mono'));
    const track = el('div', null, 'track');
    for (const segment of groups.get(key)) {
      const button = el('button', null, `segment ${segment.bucket}`);
      button.type = 'button';
      button.dataset.code = segment.code;
      button.dataset.bucket = segment.bucket;
      button.style.left = `${100 * (segment.start - window.start) / duration}%`;
      button.style.width = `${100 * segment.seconds / duration}%`;
      button.title = `${device.name} ${stamp(segment.start)} · ${buckets[segment.bucket]} · ${label(segment.code)}`;
      button.setAttribute('aria-label', button.title);
      button.setAttribute('aria-pressed', 'false');
      button.addEventListener('click', () => {
        grid.querySelector('[aria-pressed=true]')?.setAttribute('aria-pressed', 'false');
        button.setAttribute('aria-pressed', 'true');
        onSegment(segment);
      });
      track.append(button);
    }
    grid.append(name, track);
  }
  $('timeline').replaceChildren(devices.length ? grid : el('p', '暂无设备', 'empty'));
  $('legend').replaceChildren(...Object.entries(buckets).map(([key, name]) => {
    const node = el('span', null, `legend-key ${key}`);
    node.append(el('i'), name);
    return node;
  }));
  (grid.querySelector('.responsible') ?? grid.querySelector('.segment'))?.click();
}
