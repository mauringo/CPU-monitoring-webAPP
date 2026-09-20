'use strict';
const cards = new Map();
let paused = false;
const statusLabel = document.getElementById('status');
function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}
function metric(value, unit) {
    return Number.isFinite(value) ? value.toFixed(1) + unit : '—';
}
function makeCard(device) {
    const card = element('section', 'panel accelerator-card');
    const heading = element('h2');
    const source = element('p', 'accelerator-source');
    card.append(element('p', 'eyebrow', device.kind), heading, source);
    const readings = element('dl', 'accelerator-metrics');
    const values = {};
    ['Utilization', 'Video memory', 'Temperature', 'Power'].forEach(label => {
        const group = element('div');
        values[label] = element('dd', '', '—');
        group.append(element('dt', '', label), values[label]);
        readings.append(group);
    });
    const memory = element('progress');
    memory.max = 100;
    memory.setAttribute('aria-label', 'Video memory usage');
    const chart = element('div', 'accelerator-chart');
    chart.id = 'accelerator-chart-' + Math.random().toString(36).slice(2);
    chart.setAttribute('role', 'img');
    chart.setAttribute('aria-label', 'Utilization history');
    const note = element('p', 'muted');
    card.append(readings, memory, chart, note);
    return {card, heading, source, values, memory, chart, note, x: [], y: []};
}
function render(data) {
    const list = document.getElementById('accelerator-list');
    const ids = new Set(data.devices.map(device => device.id));
    for (const [id, view] of cards) {
        if (!ids.has(id)) { Plotly.purge(view.chart); view.card.remove(); cards.delete(id); }
    }
    if (!cards.size) list.replaceChildren();
    document.getElementById('summary').textContent = data.devices.length + ' devices detected · Updates every 3 seconds';
    document.getElementById('warnings').textContent = data.warnings.join(' ');
    if (!data.devices.length) list.append(element('p', 'empty-state', 'No accessible GPUs or NPUs detected. Check hardware drivers and container or Snap device permissions.'));
    data.devices.forEach(device => {
        if (!cards.has(device.id)) {
            const view = makeCard(device); cards.set(device.id, view); list.append(view.card);
        }
        const v = cards.get(device.id);
        v.heading.textContent = device.name;
        v.source.textContent = device.source + (device.driver ? ' · ' + device.driver : '');
        v.values.Utilization.textContent = metric(device.utilization, '%');
        v.values['Video memory'].textContent = Number.isFinite(device.memoryUsed) && device.memoryTotal > 0 ? metric(device.memoryUsed / 1024**3, '') + ' / ' + metric(device.memoryTotal / 1024**3, ' GiB') : '—';
        v.values.Temperature.textContent = metric(device.temperature, ' °C');
        v.values.Power.textContent = metric(device.power, ' W');
        v.memory.hidden = !Number.isFinite(device.memoryUsed) || !(device.memoryTotal > 0);
        v.memory.value = v.memory.hidden ? 0 : Math.min(100, device.memoryUsed / device.memoryTotal * 100);
        v.x.push(new Date(data.sampledAt * 1000)); v.y.push(device.utilization);
        v.x = v.x.slice(-60); v.y = v.y.slice(-60);
        loadGraph(v.chart.id, device.kind === 'GPU' ? '#2563eb' : '#008e80', 'Utilization', [0, 100], v.x, v.y);
        v.note.textContent = device.utilization === null ? 'Utilization unavailable from this driver.' : 'Utilization · last 60 samples';
    });
}
async function poll() {
    if (!paused && !document.hidden) {
        try {
            const response = await fetch('/acceleratordata', {signal: AbortSignal.timeout(10000), cache: 'no-store'});
            if (!response.ok) throw new Error('Telemetry request failed');
            const data = await response.json();
            if (!paused) {
                render(data);
                statusLabel.textContent = 'Updated ' + new Date(data.sampledAt * 1000).toLocaleTimeString();
            }
        } catch (error) {
            if (!paused) statusLabel.textContent = 'Disconnected · readings are stale · retrying';
        }
    }
    setTimeout(poll, 3000);
}
document.getElementById('pause').addEventListener('click', event => {
    paused = !paused;
    event.target.textContent = paused ? 'Resume updates' : 'Pause updates';
    event.target.setAttribute('aria-pressed', String(paused));
    statusLabel.textContent = paused ? 'Paused · readings are stale' : 'Reconnecting…';
});
poll();

window.addEventListener('monitor-theme-change', () => {
    const theme = getComputedStyle(document.documentElement);
    for (const view of cards.values()) {
        if (view.chart.data) Plotly.relayout(view.chart, {
            'font.color': theme.getPropertyValue('--muted').trim(),
            'yaxis.gridcolor': theme.getPropertyValue('--border').trim()
        });
    }
});
