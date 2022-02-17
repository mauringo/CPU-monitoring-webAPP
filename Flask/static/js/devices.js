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


function populate2() {
var mypromise=(httpGet(location.origin+"/listDevices"));
mypromise.then((data) => {
   // console.log(data);
    
    document.getElementById('Uname').innerHTML="Uname -a: "+data.uname;
    document.getElementById('Uptime').innerHTML="UUptime: "+data.uptime;
    updateTableTemp(data.cameras,"camerastable");
    updateTableTemp(data.lsusb,"lsusb");
    updateTableTemp(data.lspci,"lspci");
    
  });

}



   
      
function updateTableTemp(data,tablename) {

var rows = []
var tablecontents;

for (var i = 0; i < data.length; i++) {
    rows.push({
    
    Entry: data[i],
    
    })
    
}

//console.log(rows);
var tablecontents = ' <thead>  <tr>    <th data-field="Entry">Devices installed</th>  </tr>  </thead>';

tablecontents += "<tbody>";
for (var i = 0; i < rows.length; i++) {
    
    tablecontents += "<tr>";
    
        tablecontents += "<td>" + rows[i].Entry + "</td>";
      
        
    tablecontents += "</tr>";
    
}
tablecontents += "</tbody>";
document.getElementById(tablename).innerHTML = tablecontents;



}




function clearTable(tablename) {




var tablecontents = ' <thead>  <tr>    <th data-field="PID">PID</th>   <th data-field="Name">Name</th><th data-field="username">username</th><th data-field="RAM">RAM</th> <th data-field="CPU">CPU</th>     </tr>  </thead>';

document.getElementById(tablename).innerHTML = tablecontents;



}



