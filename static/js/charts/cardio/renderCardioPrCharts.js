export function renderCardioPrCharts(prRecords) {
  const fields = ["distance", "duration", "pace"];
  const chartIds = {
    distance: "distancePrChart",
    duration: "durationPrChart",
    pace: "pacePrChart"
  };

  // Store instances to allow destroying later
  if (!window.cardioPrChartInstances) {
    window.cardioPrChartInstances = {};
  }

  fields.forEach(field => {
    const fieldRecords = prRecords
      .filter(pr => pr.field === field && !isNaN(pr.value))
      .sort((a, b) => new Date(a.datetime) - new Date(b.datetime));

    const canvas = document.getElementById(chartIds[field]);
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    let labels, data, yAxisLabel;

    if (fieldRecords.length === 0) {
      labels = ["No Data"];
      data = [0];
      yAxisLabel = "Value";
    } else {
      labels = fieldRecords.map(pr => new Date(pr.datetime).toLocaleDateString());
      data = fieldRecords.map(pr => pr.value);
      yAxisLabel = fieldRecords[0].units || "Value";
    }

    // Destroy previous instance if it exists
    if (window.cardioPrChartInstances[field]) {
      window.cardioPrChartInstances[field].destroy();
    }

    window.cardioPrChartInstances[field] = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: `PR (${field.charAt(0).toUpperCase() + field.slice(1)})`,
          data,
          backgroundColor: "rgba(59, 130, 246, 0.2)",
          borderColor: "rgba(59, 130, 246, 1)",
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          pointRadius: fieldRecords.length === 0 ? 0 : 3,
          pointHoverRadius: fieldRecords.length === 0 ? 0 : 5
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
            suggestedMax: fieldRecords.length === 0 ? 1 : undefined
          }
        },
        plugins: {
          tooltip: {
            enabled: fieldRecords.length > 0
          },
          legend: {
            display: fieldRecords.length > 0
          }
        }
      }
    });
  });
}
