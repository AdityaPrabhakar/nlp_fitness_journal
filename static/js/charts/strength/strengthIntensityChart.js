const intensityChartCanvas = document.getElementById("strengthIntensityChart");

let strengthIntensityChart;

export function renderIntensityChart(data) {
  if (strengthIntensityChart) strengthIntensityChart.destroy();

  // Map to track how many Set #1s we've seen per date
  const sessionCountPerDate = {};
  const labels = [];

  data.forEach(d => {
    const date = d.date;

    if (d.set_number === 1) {
      // New session on this date
      sessionCountPerDate[date] = (sessionCountPerDate[date] || 0) + 1;
    }

    const sessionIndex = sessionCountPerDate[date] || 1;
    const sessionLabel = sessionCountPerDate[date] > 1 ? ` (Session ${sessionIndex})` : '';
    labels.push(`${date}\nSet #${d.set_number}${sessionLabel}`);
  });

  const intensities = data.map(d => d.relative_intensity);
  const colors = data.map(d => {
    if (d.zone === "Strength") return "rgba(239, 68, 68, 0.8)";
    if (d.zone === "Hypertrophy") return "rgba(251, 191, 36, 0.8)";
    return "rgba(59, 130, 246, 0.8)";
  });

  strengthIntensityChart = new Chart(intensityChartCanvas, {
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
              return `${d.relative_intensity.toFixed(1)}% - ${d.zone} (Set #${d.set_number}, ${d.reps} reps @ ${d.weight} lbs)`;
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
