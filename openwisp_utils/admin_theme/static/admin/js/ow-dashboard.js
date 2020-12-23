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
    let data = {
            type: 'pie',
            hole: 0.6,
        },
        element = document.createElement('div');

    // Show a graph depicting disabled graph when there is insufficient data
    if (elementsParam[i].query_params.values.length == 0) {
        data.values = [1]
        data.labels = ['Not enough data']
        data.marker = {
            colors: ['#80808091']
        }
        data.texttemplate = ' '
        data.showlegend = false
        data.hovertemplate = '%{label}'
    } else {
        data.values = elementsParam[i].query_params.values
        data.labels = elementsParam[i].query_params.labels
        data.marker = {
            colors: elementsParam[i].colors
        }
        data.texttemplate = '%{percent}<br>(%{value})'
        data.targetLink = elementsParam[i].target_link
    }

    Plotly.newPlot(element, [data], layout, options);

    if (elementsParam[i].query_params.values.length != 0) {
        element.on('plotly_click', function (data) {
            window.location = data.points[0].data.targetLink + data.points[0].label;
        });
    }
    container.appendChild(element);
}
