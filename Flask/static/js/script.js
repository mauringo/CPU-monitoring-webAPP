var switchMonitorVal= false;

function switchMonitor(){
    switchMonitorVal=! switchMonitorVal;
   
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
    
    document.getElementById('CPUReal').innerHTML+=data.phcpu;
    document.getElementById('CPUVirtual').innerHTML+=data.vrcpu;
    document.getElementById('RAMinstalled').innerHTML+=data.ram;
    document.getElementById('Architecture').innerHTML+=data.architecture;
    document.getElementById('Kernel').innerHTML+=data.kernel;
    document.getElementById('Processor').innerHTML+=data.processor;
    document.getElementById('Platform').innerHTML+=data.platform;
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

       
        document.getElementById('CPUlabel').innerHTML= 'Cpu Load : '+data.CPU +' %';
        document.getElementById('RAMlabel').innerHTML= 'RAM usage : '+data.RAM +' %';



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

    function updateTable(data,tablename) {
        
        var rows = []
        var tablecontents;
        for (var i = 0; i < data.length; i++) {
          rows.push({
           
            PID: data[i].pid,
            Name: data[i].name,
            username:data[i].username,
            RAM:data[i].vms,
            CPU:data[i].cpu_percent
          })
          
        }
       
        
        var tablecontents = ' <thead>  <tr>    <th data-field="PID">PID</th>   <th data-field="Name">Name</th><th data-field="username">username</th><th data-field="RAM">RAM</th> <th data-field="CPU">CPU</th>     </tr>  </thead>';

        tablecontents += "<tbody>";
        for (var i = 0; i < rows.length; i++) {
            
            tablecontents += "<tr>";
           
                tablecontents += "<td>" + rows[i].PID + "</td>";
                tablecontents += "<td>" + rows[i].Name + "</td>";
                tablecontents += "<td>" + rows[i].username + "</td>";
                tablecontents += "<td>" + rows[i].RAM + "</td>";
                tablecontents += "<td>" + rows[i].CPU + "</td>";
            tablecontents += "</tr>";
            
        }
        tablecontents += "</tbody>";
        document.getElementById(tablename).innerHTML = tablecontents;

       
    
      }

      function updateTableTemp(data,tablename) {
        
        var rows = []
        var tablecontents;
       
        for (var i = 0; i < data.length; i++) {
          rows.push({
           
            PID: data[i][0],
            Name: data[i][1],
            username:data[i][2],
            RAM:data[i][3]
            
          })
          
        }
       
        console.log(rows);
        var tablecontents = ' <thead>  <tr>    <th data-field="PID">Device</th>  <th data-field="username">Temperature </th><th data-field="RAM">High value</th> <th data-field="CPU">Critical Value</th>     </tr>  </thead>';

        tablecontents += "<tbody>";
        for (var i = 0; i < rows.length; i++) {
            
            tablecontents += "<tr>";
           
                tablecontents += "<td>" + rows[i].PID + "</td>";
                tablecontents += "<td>" + rows[i].Name + "</td>";
                tablecontents += "<td>" + rows[i].username + "</td>";
                tablecontents += "<td>" + rows[i].RAM + "</td>";
              
            tablecontents += "</tr>";
            
        }
        tablecontents += "</tbody>";
        document.getElementById(tablename).innerHTML = tablecontents;

       
    
      }
    
      function clearTable(tablename) {
        
        
     

        var tablecontents = ' <thead>  <tr>    <th data-field="PID">PID</th>   <th data-field="Name">Name</th><th data-field="username">username</th><th data-field="RAM">RAM</th> <th data-field="CPU">CPU</th>     </tr>  </thead>';
       
        document.getElementById(tablename).innerHTML = tablecontents;

       
    
      }


setInterval(function() {

    usageinfo();
    loadMyGraph();

}, 3000);

function loadMyGraph(){
    
    loadGraph(graph1,color1,title1,range1,CpuX, CpuY);
    loadGraph(graph2,color2,title2,range2,CpuX, RamY);
}




var graph1='CPUgraph';
var color1='#0079fc';
var data1='CPU';
var range1=[0, 100];
var title1='CPU %';

var graph2='RAMgraph';
var color2='#27a849';
var data2='RAM';
var range2=[0, 100];
var title2='RAM %';
            
var CpuX=[];
var CpuY=[];
var RamX=[];
var RamY=[];    
