var switchMonitorVal= false;

function switchMonitor(){
    switchMonitorVal=! switchMonitorVal;
    const button = document.getElementById('task-toggle');
    button.setAttribute('aria-pressed', String(switchMonitorVal));
    button.textContent = switchMonitorVal ? 'Pause task monitor' : 'Enable task monitor';
    if (switchMonitorVal) processesInfo();
   
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
  });

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
        else{
            clearTable("cputable");
            clearTable("ramtable");
        }
        });
      
    }

    function processesInfo() {
        var mypromise=httpGet(location.origin+"/processes");

        mypromise.then((data) => {
            
            
            updateTable(data.cpuProcesses,"cputable");
            updateTable(data.ramProcesses,"ramtable");
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

function updateTable(data, tablename) {
    renderTable(tablename, ['PID', 'Name', 'User', 'Virtual RAM (MiB)', 'CPU'],
        data.map(row => [row.pid, row.name, row.username, displayNumber(row.vms), displayNumber(row.cpu_percent, '%')]),
        'No processes available.');
}

function updateTableTemp(data, tablename) {
    renderTable(tablename, ['Device', 'Temperature', 'High', 'Critical'],
        data.map(row => [row[0], ...row.slice(1).map(value => displayNumber(value, ' °C'))]),
        'No temperature sensors detected or accessible.');
}

function clearTable(tablename) {
    renderTable(tablename, ['PID', 'Name', 'User', 'Virtual RAM (MiB)', 'CPU'], [],
        'Enable the task monitor to view processes.');
}

setInterval(function() {

    usageinfo();

}, 3000);

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
