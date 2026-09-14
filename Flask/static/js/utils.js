function loadGraph(graph, color, title, range, xpoints, ypoints) {
    const fill = graph === 'CPUgraph' ? 'rgba(37,99,235,0.08)' : 'rgba(0,142,128,0.08)';
    return Plotly.react(graph, [{
        type: 'scatter', mode: xpoints.length < 2 ? 'lines+markers' : 'lines', marker: {size: 6, color}, name: title,
        x: xpoints.slice(-60), y: ypoints.slice(-60),
        line: {color, width: 2.5, shape: 'linear'},
        fill: 'tozeroy', fillcolor: fill,
        hovertemplate: '%{y:.1f}%<extra></extra>'
    }], {
        margin: {l: 32, r: 8, t: 12, b: 25}, height: 210,
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: {family: 'system-ui, sans-serif', color: '#8191a5', size: 10},
        xaxis: {nticks: 4, showgrid: false, zeroline: false, fixedrange: true},
        yaxis: {range, ticksuffix: '%', dtick: 25, gridcolor: '#edf1f6', zeroline: false, fixedrange: true},
        showlegend: false
    }, {responsive: true, displayModeBar: false, scrollZoom: false});
}
