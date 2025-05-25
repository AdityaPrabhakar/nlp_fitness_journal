const volumeChartCanvas = document.getElementById("strengthVolumeChart");

let strengthVolumeChart;

export function renderVolumeChart(data) {
  if (strengthVolumeChart) strengthVolumeChart.destroy();
  strengthVolumeChart = new Chart(volumeChartCanvas, {
    type: 'line',
    data: {
      labels: data.map(d => d.date),
      datasets: [{
        label: "Total Volume",
        data: data.map(d => d.volume),
        borderColor: "rgb(16, 185, 129)",
        backgroundColor: "rgba(16, 185, 129, 0.2)",
        tension: 0.2,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      scales: {
        y: {
          title: { display: true, text: 'Volume (lbs)' },
          beginAtZero: true
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