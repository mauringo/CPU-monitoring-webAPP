let devicesLoading = false;
async function populate2(section = null) {
    if (devicesLoading) return;
    devicesLoading = true;
    const buttons = document.querySelectorAll('[data-refresh]');
    buttons.forEach(button => { button.disabled = true; });
    document.getElementById('refresh-status').textContent = 'Refreshing hardware…';
    const tables = {cameras: 'camerastable', lsusb: 'lsusb', lspci: 'lspci', nvme: 'nvmetable', npus: 'nputable'};
    try {
        const response = await fetch('/listDevices');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        document.getElementById('Uname').textContent = 'Uname -a: ' + (data.uname || []).join(' ');
        document.getElementById('Uptime').textContent = 'Uptime: ' + (data.uptime || []).join(' ');
        for (const [key, table] of Object.entries(tables)) {
            if (section && key !== section) continue;
            updateDeviceTable(data[key], table, 'No devices detected or accessible. Drivers or hardware permissions may be required.');
            document.getElementById(table + '-updated').textContent = 'Updated ' + new Date().toLocaleTimeString();
        }
        document.getElementById('refresh-status').textContent = 'Updated ' + new Date().toLocaleTimeString();
    } catch (error) {
        for (const [key, table] of Object.entries(tables)) {
            if (section && key !== section) continue;
            updateDeviceTable([], table, 'Unable to load devices. Try Update Values again.');
        }
        document.getElementById('refresh-status').textContent = 'Refresh failed · try again';
        console.error('Device discovery failed:', error);
    } finally {
        devicesLoading = false;
        buttons.forEach(button => { button.disabled = false; });
    }
}

function updateDeviceTable(devices, id, emptyMessage) {
    const table = document.getElementById(id);
    const count = Array.isArray(devices) ? devices.length : 0;
    document.getElementById(id + '-count').textContent = count ? count + (count === 1 ? ' entry' : ' entries') : 'None detected';
    const body = document.createElement('tbody');
    const rows = Array.isArray(devices) && devices.length ? devices : [emptyMessage];
    for (const device of rows) {
        const cell = body.insertRow().insertCell();
        cell.textContent = device;
        if (!count) cell.className = "empty-state";
    }
    if (table.tBodies.length) table.tBodies[0].replaceWith(body);
    else table.appendChild(body);
}
