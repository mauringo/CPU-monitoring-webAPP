function escapeHtml(value) {
    const span = document.createElement('span');
    span.textContent = value == null ? '' : String(value);
    return span.innerHTML;
}

var switchMonitorVal = false;
var refreshTimer;
var processRows = {cpu: [], ram: []};
var themeModes = ['system', 'light', 'dark'];
var savedTheme = localStorage.getItem('cpu-monitor-theme');
var themeMode = themeModes.includes(savedTheme) ? savedTheme : 'system';

function switchMonitor(){
    switchMonitorVal = !switchMonitorVal;
    const button = document.getElementById('task-toggle');
    button.setAttribute('aria-pressed', String(switchMonitorVal));
    button.textContent = switchMonitorVal ? 'Pause task monitor' : 'Enable task monitor';
    if (switchMonitorVal) processesInfo();
    else {
        clearTable('cputable');
        clearTable('ramtable');
    }
}


function httpGet(theUrl) {   let reqHeader = new Headers();
    reqHeader.append('Content-Type', 'text/json');
    let initObject = {
        method: 'GET', headers: reqHeader,
    };

    return fetch(theUrl,initObject)
        .then((response) => { 
            return response.json().then((data) => {
                //console.log(data);
                return data;
            }).catch((err) => {
                console.log(err);
            }) 
        });

}


function populate() {
applyTheme();
loadPermissions();
document.addEventListener('click', closeHelpWhenClickedOutside);
document.querySelector('.info-menu').addEventListener('toggle', refreshPermissionsWhenOpened);
document.getElementById('refresh-rate').addEventListener('change', scheduleRefresh);
document.getElementById('process-search').addEventListener('input', renderProcessTables);
document.getElementById('theme-toggle').textContent = 'Theme: ' + themeMode;
var mypromise=(httpGet(location.origin+"/staticdata"));
mypromise.then((data) => {
    //console.log(data);
    
    document.getElementById('CPUReal').textContent=data.phcpu;
    document.getElementById('CPUVirtual').textContent=data.vrcpu;
    document.getElementById('RAMinstalled').textContent=data.ram;
    document.getElementById('Architecture').textContent=data.architecture;
    document.getElementById('Kernel').textContent=data.kernel;
    document.getElementById('Processor').textContent=data.processor;
    document.getElementById('Platform').textContent=data.platform;
    usageinfo();
    scheduleRefresh();
  });

}

function closeHelpWhenClickedOutside(event) {
    const menu = document.querySelector('.info-menu');
    if (menu && menu.open && !menu.contains(event.target)) menu.removeAttribute('open');
}

function refreshPermissionsWhenOpened(event) {
    if (event.target.open) loadPermissions();
}

async function loadPermissions() {
    const menu = document.getElementById('permission-menu');
    try {
        const report = await httpGet(location.origin + '/permissions');
        const interfaces = Object.entries(report.interfaces || {});
        const commands = Object.entries(report.commands || {});
        const interfaceRows = interfaces.map(([name, item]) => {
            const state = item.connected === true ? 'connected' : item.connected === false ? 'not connected' : 'unknown';
            return '<li><span class="permission-dot ' + state.replace(' ', '-') + '"></span><span><strong>' + name + '</strong><small>' + item.purpose + '</small></span><em>' + state + '</em></li>';
        }).join('');
        const commandRows = commands.map(([name, available]) => '<li><code>' + name + '</code><em>' + (available ? 'available' : 'missing') + '</em></li>').join('');
        menu.innerHTML = '<div class="permission-heading"><strong>Runtime access</strong><span>' + (report.confinement || 'unknown') + '</span></div><ul class="permission-list">' + interfaceRows + '</ul><div class="permission-heading"><strong>Utilities</strong></div><ul class="permission-commands">' + commandRows + '</ul><p class="permission-help">Connect all interfaces:</p><div class="command-copy"><textarea id="connect-command" class="permission-command" readonly aria-label="Command to connect all interfaces"></textarea><button class="btn btn-outline-primary btn-sm" type="button" onclick="copyPermissionCommand()">Copy command</button></div><p class="permission-help">For local testing only, use: <strong>' + report.devmode + '</strong></p><p class="permission-disclaimer">Disclaimer: use at your own risk.</p>';
        document.getElementById('connect-command').value = report.connectAll;
    } catch (error) {
        menu.innerHTML = '<p class="permission-loading">Permission check unavailable.</p>';
        console.error('Permission check failed:', error);
    }
}

async function copyPermissionCommand() {
    const field = document.getElementById('connect-command');
    const button = field.nextElementSibling;
    try {
        await navigator.clipboard.writeText(field.value);
    } catch (error) {
        field.select();
        document.execCommand('copy');
    }
    button.textContent = 'Copied';
    setTimeout(() => { button.textContent = 'Copy command'; }, 1600);
}





function download_csv() {
    var csv = 'Cpu,CpuTime,Ram,Ramtime\n';
    for (let i = 0; i < CpuX.length; i++) {
        csv += CpuY[i] + ',' + CpuX[i]+ ',' +  RamY[i] + ',' + RamX[i];
        csv += "\n";
        }
    
    
   // console.log(csv);
    var hiddenElement = document.createElement('a');
    hiddenElement.href = 'data:text/csv;charset=utf-8,' + encodeURI(csv);
    hiddenElement.target = '_blank';
    hiddenElement.download = 'CPU_RAM_usage.csv';
    hiddenElement.click();
}

    

function usageinfo() {
    var mypromise=httpGet(location.origin+"/usagedata");

    mypromise.then((data) => {
        console.log(data.temp);
            
            
        
        $('#cpu').attr('aria-valuenow', data.CPU).css('width', `${data.CPU}%`);
        $('#RAM').attr('aria-valuenow', data.RAM).css('width', `${data.RAM}%`);
        $('#Thermal').attr('placeholder', data.temp);
        updateTableTemp(data.temp,"temperature");

       
        document.getElementById('cpu-value').innerHTML=Number(data.CPU).toFixed(1)+'<span>%</span>';
        document.getElementById('RAM-value').innerHTML=Number(data.RAM).toFixed(1)+'<span>%</span>';
        renderCoreUsage(data.perCpu || []);
        renderResourceUsage(data.network || {}, data.disk || {});
        document.getElementById('refresh-status').textContent='Updated '+new Date().toLocaleTimeString();



        unix_timestamp=Date.now();
        var date = new Date(unix_timestamp * 1);
        // Hours part from the timestamp
        var hours = date.getHours();
        // Minutes part from the timestamp
        var minutes = "0" + date.getMinutes();
        // Seconds part from the timestamp
        var seconds = "0" + date.getSeconds();

        // Will display time in 10:30:23 format
        var formattedTime = hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);

        CpuY.push(data.CPU);
        RamY.push(data.RAM);
        CpuX.push(formattedTime);
        RamX.push(formattedTime);

        if (CpuX.length > 10000) {
            CpuX.shift();
            CpuY.shift();
            RamX.shift();
            RamY.shift();
        }
        
        loadMyGraph();

        if (switchMonitorVal){
            processesInfo();
        }
        });
      
    }

    function processesInfo() {
        var mypromise=httpGet(location.origin+"/processes");

        mypromise.then((data) => {
            
            
            processRows.cpu = data.cpuProcesses || [];
            processRows.ram = data.ramProcesses || [];
            renderProcessTables();
            });
            
        }

function displayNumber(value, unit = '') {
    return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString(undefined, {maximumFractionDigits: 1}) + unit : '—';
}

function renderTable(id, headers, rows, message) {
    const table = document.getElementById(id);
    const head = document.createElement('thead');
    const heading = head.insertRow();
    headers.forEach(label => {
        const cell = document.createElement('th');
        cell.scope = 'col';
        cell.textContent = label;
        heading.appendChild(cell);
    });
    const body = document.createElement('tbody');
    rows.forEach(values => {
        const row = body.insertRow();
        values.forEach(value => { row.insertCell().textContent = value == null ? '—' : value; });
    });
    if (!rows.length) {
        const cell = body.insertRow().insertCell();
        cell.colSpan = headers.length;
        cell.className = 'empty-state';
        cell.textContent = message;
    }
    table.replaceChildren(head, body);
}

function renderProcessTable(data, tablename) {
    const table = document.getElementById(tablename);
    const body = document.createElement('tbody');
    data.forEach(row => {
        const cells = [row.pid, row.name, row.username, displayNumber(row.rss, ' MiB'), displayNumber(row.cpu_percent, '%')];
        const tr = body.insertRow();
        cells.forEach(value => tr.insertCell().textContent = value == null ? '—' : value);
        const action = tr.insertCell();
        const button = document.createElement('button');
        button.className = 'btn btn-outline-danger btn-sm process-action';
        button.type = 'button';
        button.textContent = 'Stop';
        button.title = 'Terminate process ' + row.pid;
        button.addEventListener('click', () => terminateProcess(row.pid, row.name));
        action.appendChild(button);
    });
    if (!data.length) {
        const cell = body.insertRow().insertCell();
        cell.colSpan = 6;
        cell.className = 'empty-state';
        cell.textContent = 'No matching processes available.';
    }
    table.tBodies[0].replaceWith(body);
}

function renderProcessTables() {
    const query = (document.getElementById('process-search').value || '').toLowerCase();
    const matches = rows => rows.filter(row => [row.pid, row.name, row.username].join(' ').toLowerCase().includes(query));
    renderProcessTable(matches(processRows.cpu), 'cputable');
    renderProcessTable(matches(processRows.ram), 'ramtable');
}

async function terminateProcess(pid, name) {
    if (!confirm('Terminate ' + (name || 'process') + ' (' + pid + ')?')) return;
    const token = prompt('Process-control token (configured on the server):');
    if (!token) return;
    const response = await fetch('/processes/' + pid + '/terminate', {method: 'POST', headers: {'Authorization': 'Bearer ' + token}});
    if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        alert(result.error || 'Unable to terminate process.');
        return;
    }
    processesInfo();
}

function updateTableTemp(data, tablename) {
    renderTable(tablename, ['Device', 'Temperature', 'High', 'Critical'],
        data.map(row => [row[0], ...row.slice(1).map(value => displayNumber(value, ' °C'))]),
        'No temperature sensors detected or accessible.');
}

function clearTable(tablename) {
    renderTable(tablename, ['PID', 'Name', 'User', 'Virtual RAM (MiB)', 'CPU', 'Action'], [],
        'Enable the task monitor to view processes.');
}

function formatBytes(value) {
    if (!Number.isFinite(value)) return '—';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = value;
    let unit = 0;
    while (size >= 1024 && unit < units.length - 1) { size /= 1024; unit++; }
    return size.toLocaleString(undefined, {maximumFractionDigits: 1}) + ' ' + units[unit];
}

function renderCoreUsage(values) {
    const grid = document.getElementById('core-grid');
    grid.replaceChildren();
    values.forEach((value, index) => {
        const item = document.createElement('div');
        item.className = 'core-item';
        item.innerHTML = '<div><span>Core ' + (index + 1) + '</span><strong>' + Number(value).toFixed(1) + '%</strong></div><div class="progress"><div class="progress-bar" style="width:' + value + '%" role="progressbar" aria-valuenow="' + value + '" aria-valuemin="0" aria-valuemax="100"></div></div>';
        grid.appendChild(item);
    });
    if (!values.length) grid.innerHTML = '<p class="empty-state">Per-core readings unavailable.</p>';
}

function renderResourceUsage(network, disk) {
    document.getElementById('network-received').textContent = formatBytes(network.received);
    document.getElementById('network-sent').textContent = formatBytes(network.sent);
    const interfaces = document.getElementById('network-interfaces');
    interfaces.replaceChildren();
    if (!network.interfaces || !network.interfaces.length) {
        interfaces.innerHTML = '<p class="empty-state">No network interfaces detected.</p>';
    } else {
        network.interfaces.forEach(device => {
            const item = document.createElement('div');
            item.className = 'core-item disk-item network-item';
            item.innerHTML = '<div><span>' + escapeHtml(device.name) + '</span><strong>' + escapeHtml((device.addresses || []).join(' · ') || 'No address reported') + '</strong></div>';
            interfaces.appendChild(item);
        });
    }
    const list = document.getElementById('disk-list');
    list.replaceChildren();
    if (!disk.disks || !disk.disks.length) {
        list.innerHTML = '<p class="empty-state">No physical disks detected or accessible.</p>';
        return;
    }
    disk.disks.forEach(device => {
        const item = document.createElement('div');
        item.className = 'core-item disk-item network-item';
        const filesystems = device.filesystems || [];
        const details = [device.model, device.mountpoint, device.filesystem].filter(Boolean).join(' · ');
        const volumeRows = filesystems.map(filesystem => {
            const percent = Number.parseFloat(filesystem.usedPercent);
            const label = filesystem.mountpoint || ('/dev/' + filesystem.name);
            const metadata = [label, filesystem.filesystem, Number.isFinite(percent) ? percent + '% used' : 'usage unavailable'].filter(Boolean).join(' · ');
            return '<div class="disk-volume"><div><span>' + escapeHtml(metadata) + '</span></div><div class="progress"><div class="progress-bar" style="width:' + (Number.isFinite(percent) ? percent : 0) + '%" role="progressbar" aria-valuenow="' + (Number.isFinite(percent) ? percent : 0) + '" aria-valuemin="0" aria-valuemax="100"></div></div></div>';
        }).join('');
        item.innerHTML = '<div><span>/dev/' + escapeHtml(device.name) + '</span><strong>' + formatBytes(device.size) + '</strong></div><small>' + escapeHtml(details || 'No mounted filesystem') + '</small>' + (volumeRows || '<small>No mounted filesystem usage</small>');
        list.appendChild(item);
    });
}

function scheduleRefresh() {
    clearInterval(refreshTimer);
    const interval = Number(document.getElementById('refresh-rate').value);
    refreshTimer = setInterval(usageinfo, interval);
}

function applyTheme() {
    document.documentElement.dataset.theme = themeMode;
}

function cycleTheme() {
    themeMode = themeModes[(themeModes.indexOf(themeMode) + 1) % themeModes.length];
    localStorage.setItem('cpu-monitor-theme', themeMode);
    applyTheme();
    document.getElementById('theme-toggle').textContent = 'Theme: ' + themeMode;
}

function loadMyGraph(){
    
    loadGraph(graph1,color1,title1,range1,CpuX, CpuY);
    loadGraph(graph2,color2,title2,range2,RamX, RamY);
}




var graph1='CPUgraph';
var color1='#2563eb';
var data1='CPU';
var range1=[0, 100];
var title1='CPU %';

var graph2='RAMgraph';
var color2='#008e80';
var data2='RAM';
var range2=[0, 100];
var title2='RAM %';
            
var CpuX=[];
var CpuY=[];
var RamX=[];
var RamY=[];    
