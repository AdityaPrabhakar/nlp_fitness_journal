import { authFetch } from "../../auth/authFetch.js";

let sessionDetailChart = null;

export async function renderDetailedSessionsChart(exercise, startDate, endDate) {
  const container = document.getElementById("sessionChartContainer");
  container.innerHTML = "<canvas id='sessionChart'></canvas>";

  const ctx = document.getElementById("sessionChart").getContext("2d");

  const params = new URLSearchParams({ exercise });
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  try {
    const res = await authFetch(`/api/sessions/by-exercise?${params}`);
    const data = await res.json();

    if (!Array.isArray(data) || data.length === 0) {
      container.innerHTML = "<p class='text-center text-gray-500'>No session data available.</p>";
      return;
    }

    const labels = [];
    const weightData = [];
    const repsData = [];

    const sessionCountPerDate = {};

    data.forEach(session => {
      const sessionDate = session.date;

      let isNewSession = true;

      session.entries.forEach(entry => {
        if (entry.type === "strength") {
          entry.sets.forEach(set => {
            if (set.set_number === 1 && isNewSession) {
              sessionCountPerDate[sessionDate] = (sessionCountPerDate[sessionDate] || 0) + 1;
              isNewSession = false;
            }

            const sessionIndex = sessionCountPerDate[sessionDate] || 1;
            const sessionLabel = sessionCountPerDate[sessionDate] > 1 ? ` (Session ${sessionIndex})` : '';
            labels.push(`${sessionDate} - Set #${set.set_number}${sessionLabel}`);
            weightData.push(set.weight);
            repsData.push(set.reps);
          });
        }
      });
    });

    if (sessionDetailChart) sessionDetailChart.destroy();

    sessionDetailChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Weight (kg)",
            type: "bar",
            data: weightData,
            backgroundColor: "rgba(59, 130, 246, 0.6)",
            borderColor: "rgba(59, 130, 246, 1)",
            borderWidth: 1,
            yAxisID: "yWeight"
          },
          {
            label: "Reps",
            type: "bar",
            data: repsData,
            backgroundColor: "rgba(34, 197, 94, 0.6)",
            borderColor: "rgba(34, 197, 94, 1)",
            borderWidth: 1,
            yAxisID: "yReps"
          }
        ]
      },
      options: {
        responsive: true,
        interaction: {
          mode: "index",
          intersect: false
        },
        scales: {
          x: {
            ticks: {
              autoSkip: true,
              maxRotation: 60,
              minRotation: 45,
              callback: function(value, index, ticks) {
                const label = this.getLabelForValue(value);
                return label.length > 30 ? label.slice(0, 30) + "…" : label;
              }
            }
          },
          yWeight: {
            type: "linear",
            position: "left",
            beginAtZero: true,
            title: { display: true, text: "Weight (kg)" }
          },
          yReps: {
            type: "linear",
            position: "right",
            beginAtZero: true,
            grid: { drawOnChartArea: false },
            title: { display: true, text: "Reps" }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: ${context.parsed.y}`;
              }
            }
          },
          legend: {
            labels: {
              filter: item => item.text !== undefined
            }
          }
        }
      }
    });

  } catch (err) {
    console.error("[detailedSessionsChart] Error:", err);
    container.innerHTML = "<p class='text-center text-red-500'>Failed to load chart.</p>";
  }
}
