
            


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
        
      
        }
    
    setInterval(function() {
    
        usageinfo();
    
   
    }, 3000);

    
