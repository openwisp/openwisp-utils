"use strict";

let elementsParam = Object.values(dashboardConfig),
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
            x: 1,
            y: 0.05,
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
    };

for (let i = 0; i < elementsParam.length; ++i) {
    layout.title.text = elementsParam[i].name;
    let data = [{
            values: elementsParam[i].query_params.values,
            labels: elementsParam[i].query_params.labels,
            marker: {
                colors: elementsParam[i].colors
            },
            type: 'pie',
            hole: 0.6,
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
