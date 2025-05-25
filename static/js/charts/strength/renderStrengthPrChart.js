export function renderStrengthPrChart(prRecords) {
  const ctx = document.getElementById("prChart").getContext("2d");

  const sorted = prRecords
    .filter(pr => !isNaN(pr.value))
    .sort((a, b) => new Date(a.datetime) - new Date(b.datetime));

  let labels, data, yAxisLabel;

  if (sorted.length === 0) {
    labels = ["No Data"];
    data = [0];
    yAxisLabel = "Value";
  } else {
    labels = sorted.map(pr => new Date(pr.datetime).toLocaleDateString());
    data = sorted.map(pr => pr.value);
    yAxisLabel = sorted[0].units ? `${sorted[0].units}` : 'Value';
  }

  if (window.prChartInstance) {
    window.prChartInstance.destroy();
  }

  window.prChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: `PR (${yAxisLabel})`,
        data,
        backgroundColor: "rgba(34, 197, 94, 0.2)",
        borderColor: "rgba(34, 197, 94, 1)",
        borderWidth: 2,
        fill: true,
        tension: 0.3,
        pointRadius: sorted.length === 0 ? 0 : 3,
        pointHoverRadius: sorted.length === 0 ? 0 : 5
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: {
          title: { display: true, text: "Date" }
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: yAxisLabel },
          suggestedMax: sorted.length === 0 ? 1 : undefined
        }
      },
      plugins: {
        tooltip: {
          enabled: sorted.length > 0
        },
        legend: {
          display: sorted.length > 0
        }
      }
    }
  });
}
