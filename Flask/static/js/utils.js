
  
  
  function loadGraph(graph,color,title,range,xpoints,ypoints) {
  
   
    var firstTrace = {
      type: 'scatter',
      mode: 'lines',
      name: 'Mean User Usage',
      borderWidth: 0,
      x: xpoints,
      y: ypoints,
      line: {color: color,
             shape: 'spline', 
             smoothing: 0.2,
             width: 4}
    }
    
    var datag = [firstTrace];
    var config = {
      responsive: true,
      displaylogo: false,
      displayModeBar: false,
      editable: false,
      dragMode:false,
      scrollZoom:false
      }
    var layout = {
      title: title,
      yaxis: {
        autorange: false,
        range: range,
        boundmode: 'soft',
        bounds: range}
    };
  
    return Plotly.newPlot(graph, datag, layout, config);
    //window.myLine = new Chart(ctx, config);
    
    
  }
  
  
