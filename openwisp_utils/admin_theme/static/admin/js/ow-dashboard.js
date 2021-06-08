(function() {
  'use strict';

  let elementsParam = Object.values(owDashboardCharts),
      container = document.getElementById('plot-container');

  const layout = {
    height: 450,
    width: 450,
    margin: {
      t: 0,
      b: 0
    },
    legend: {
      yanchor: 'center',
      xanchor: 'left',
      x: 0,
      y: 0,
      bgcolor: 'transparent'
    },
    title: {
      yanchor: 'center',
      y: 0.92,
      font: {size: 20}
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
      data.values = [1];
      data.labels = ['Not enough data'];
      data.marker = {
        colors: ['#80808091']
      };
      data.texttemplate = ' ';
      data.showlegend = false;
      data.hovertemplate = '%{label}';
    } else {
      data.values = elementsParam[i].query_params.values;
      data.labels = elementsParam[i].query_params.labels;

      if (data.labels.length > 4) {
        data.showlegend = false;
      }
      data.rotation = 180;
      data.textposition = 'inside';
      data.insidetextorientation = 'horizontal';

      if (elementsParam[i].colors) {
        data.marker = {
          colors: elementsParam[i].colors
        };
      }
      data.texttemplate = '<b>%{value}</b><br>(%{percent})';
      data.targetLink = elementsParam[i].target_link;
      data.filters = elementsParam[i].filters;

      // add total to pie chart
      var total = 0;
      for (var c = 0; c < data.values.length; c++) {
        total += data.values[c];
      }
      layout.annotations = [
        {
          font: {
            size: 20,
            weight: 'bold'
          },
          showarrow: false,
          text: `<b>${total}</b>`,
          x: 0.5,
          y: 0.5
        }
      ];
    }

    Plotly.newPlot(element, [data], layout, options);

    if (elementsParam[i].query_params.values.length !== 0) {
      element.on('plotly_click', function (data) {
        var path = data.points[0].data.targetLink,
            filters = data.points[0].data.filters,
            i = data.points[0].i;
        if (filters && typeof(filters[i]) !== 'undefined') {
          path += filters[i];
        } else {
          path += encodeURIComponent(data.points[0].label);
        }
        window.location = path;
      });
    }
    container.appendChild(element);
  }

})();
