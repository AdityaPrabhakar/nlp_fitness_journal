const intensityChartCanvas = document.getElementById("intensityChart");

let intensityChart;

export function renderIntensityChart(data) {
  if (intensityChart) intensityChart.destroy();

  const labels = data.map((d, i) => `${d.date}\nSet #${i + 1}`);
  const intensities = data.map(d => d.relative_intensity);
  const colors = data.map(d => {
    if (d.zone === "Strength") return "rgba(239, 68, 68, 0.8)";
    if (d.zone === "Hypertrophy") return "rgba(251, 191, 36, 0.8)";
    return "rgba(59, 130, 246, 0.8)";
  });

  intensityChart = new Chart(intensityChartCanvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: "Relative Intensity (%1RM)",
        data: intensities,
        backgroundColor: colors,
        borderWidth: 1
      }]
    },
    options: {
      plugins: {
        tooltip: {
          callbacks: {
            label: function (ctx) {
              const d = data[ctx.dataIndex];
              return `${d.relative_intensity.toFixed(1)}% - ${d.zone}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 110,
          title: { display: true, text: "% of 1RM" }
        },
        x: {
          title: { display: true, text: "Set (Date & Order)" },
          ticks: {
            maxRotation: 0,
            minRotation: 0,
            autoSkip: false
          }
        }
      }
    }
  });
}