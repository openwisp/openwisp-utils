"use strict";

let elementsName = Object.keys(dashboardSchema),
    elementsParam = Object.values(dashboardSchema),
    container = document.getElementById('plot-container');

const layout = {
        height: 400,
        width: 400,
        margin: {
            t: 0,
            b: 0
        }
    },
    options = {
        displayModeBar: false,
        responsive: true
    };

for (let i = 0; i < elementsParam.length; ++i) {
    let data = [{
        values: elementsParam[i].query_params.values,
        labels: elementsParam[i].query_params.labels,
        type: 'pie',
        hole: 0.65,
        title: {
            text: elementsName[i],
            font: {
                size: 20
            },
            position: 'bottom center'
        },
        targetLink: elementsParam[i].target_link
    }], element = document.createElement('div');

    Plotly.newPlot(element, data, layout, options);

    element.on('plotly_click', function (data) {
        window.location = data.points[0].data.targetLink + data.points[0].label;
    });

    container.appendChild(element);
}
