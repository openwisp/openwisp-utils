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
        },
        legend: {
            yanchor: 'bottom',
            xanchor: 'center',
            x: 0.5,
            y: 0.1,
            orientation: 'h'
        },
        title: {
            yanchor: 'top',
            y: 0.88,
            font: {
                size: 20
            }
        }
    },
    options = {
        displayModeBar: false,
        responsive: true
    };

for (let i = 0; i < elementsParam.length; ++i) {
    layout.title.text = elementsName[i]
    let data = [{
            values: elementsParam[i].query_params.values,
            labels: elementsParam[i].query_params.labels,
            marker: {
                colors: elementsParam[i].colors
            },
            type: 'pie',
            hole: 0.65,
            targetLink: elementsParam[i].target_link,
            texttemplate: '%{percent}<br>(%{value})'
        }],
        element = document.createElement('div');

    Plotly.newPlot(element, data, layout, options);

    element.on('plotly_click', function (data) {
        window.location = data.points[0].data.targetLink + data.points[0].label;
    });

    container.appendChild(element);
}
