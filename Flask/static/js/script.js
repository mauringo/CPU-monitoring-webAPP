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

    function httpGet(theUrl)
    {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", theUrl, false ); // false for synchronous request
    xmlHttp.send( null );
    return xmlHttp.responseText;
    }

    
    function populate() {
    var data=JSON.parse(httpGet(location.origin+"/staticdata"));
   
    document.getElementById('CPUReal').innerHTML+=data.phcpu;
    document.getElementById('CPUVirtual').innerHTML+=data.vrcpu;
    document.getElementById('RAMinstalled').innerHTML+=data.ram;
    document.getElementById('Architecture').innerHTML+=data.architecture;
    document.getElementById('Kernel').innerHTML+=data.kernel;
    document.getElementById('Processor').innerHTML+=data.processor;
    document.getElementById('Platform').innerHTML+=data.platform;
    usageinfo();
    }

    function usageinfo() {
        var data=JSON.parse(httpGet(location.origin+"/usagedata"));

     
        $('#cpu').attr('aria-valuenow', data.CPU).css('width', `${data.CPU}%`);
        $('#RAM').attr('aria-valuenow', data.RAM).css('width', `${data.RAM}%`);
        $('#Thermal').attr('placeholder', data.temp);

        $('#CPUlabel').attr('aria-valuenow', data.CPU).css('width', `${data.CPU}%`);
        $('#RAMlabel').attr('aria-valuenow', data.RAM).css('width', `${data.RAM}%`);
       
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
        }
    
    setInterval(function() {
    
        usageinfo();
        loadMyGraph();
   
    }, 3000);

    function loadMyGraph(){
        
        loadGraph(graph1,color1,title1,range1,CpuX, CpuY);
        loadGraph(graph2,color2,title2,range2,CpuX, RamY);
    
      
        
    }

    
