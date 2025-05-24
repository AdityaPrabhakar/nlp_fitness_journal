export function renderPrChart(prRecords) {
  const ctx = document.getElementById("prChart").getContext("2d");

  const sorted = prRecords
    .filter(pr => !isNaN(pr.value))
    .sort((a, b) => new Date(a.datetime) - new Date(b.datetime));

  const labels = sorted.map(pr => new Date(pr.datetime).toLocaleDateString());
  const data = sorted.map(pr => pr.value);

  // Infer PR type: assumes all records are of the same type
  const prType = sorted.length > 0 ? sorted[0].type : null;
  let yAxisLabel = "Value";

  if (prType === "weight") {
    yAxisLabel = "Weight (lbs)";
  } else if (prType === "reps") {
    yAxisLabel = "Reps";
  }

  if (window.prChartInstance) {
    window.prChartInstance.destroy();
  }

  window.prChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "PR Value",
        data,
        backgroundColor: "rgba(34, 197, 94, 0.2)",
        borderColor: "rgba(34, 197, 94, 1)",
        borderWidth: 2,
        fill: true,
        tension: 0.3
      }]
    },
    options: {
      scales: {
        x: {
          title: { display: true, text: "Date" }
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: yAxisLabel }
        }
      }
    }
  });
}
