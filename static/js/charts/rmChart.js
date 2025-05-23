const rmChartCanvas = document.getElementById("rmChart");

let rmChart;

export function renderRmChart(data) {
  if (rmChart) rmChart.destroy();
  rmChart = new Chart(rmChartCanvas, {
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
          title: { display: true, text: 'Date' }
        }
      }
    }
  });
}
