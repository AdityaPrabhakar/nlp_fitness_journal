const volumeChartCanvas = document.getElementById("volumeChart");

let volumeChart;

export function renderVolumeChart(data) {
  if (volumeChart) volumeChart.destroy();
  volumeChart = new Chart(volumeChartCanvas, {
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
          title: { display: true, text: 'Date' }
        }
      }
    }
  });
}