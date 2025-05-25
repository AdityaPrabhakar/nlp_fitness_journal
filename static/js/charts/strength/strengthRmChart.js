const rmChartCanvas = document.getElementById("strengthRmChart");

let strengthRmChart;

export function renderRmChart(data) {
  if (strengthRmChart) strengthRmChart.destroy();
  strengthRmChart = new Chart(rmChartCanvas, {
    type: 'line',
    data: {
      labels: data.map(d => d.date),
      datasets: [{
        label: "Estimated 1RM",
        data: data.map(d => d.estimated_1rm),
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.2)",
        tension: 0.2,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      scales: {
        y: {
          title: { display: true, text: '1RM (lbs)' },
          beginAtZero: false
        },
        x: {
          title: { display: true, text: 'Date' },
          ticks: {
            autoSkip: true,
            maxRotation: 60,
            minRotation: 45,
            callback: function(value, index, ticks) {
              const label = this.getLabelForValue(value);
              return label.length > 30 ? label.slice(0, 30) + "…" : label;
            }
          }
        }
      }
    }
  });
}
