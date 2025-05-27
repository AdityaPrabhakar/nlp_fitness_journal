import { authFetch } from "../../auth/authFetch.js";

let sessionDetailChart = null;
let paceChart = null;

export async function renderCardioDetailedSessionsChart(exercise, startDate, endDate) {
  const container = document.getElementById("sessionChartContainer");
  container.innerHTML = `
    <canvas id='sessionChart'></canvas>
    <div class="mt-8">
      <canvas id='paceChart'></canvas>
    </div>
  `;

  const ctx = document.getElementById("sessionChart").getContext("2d");
  const paceCtx = document.getElementById("paceChart").getContext("2d");

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
    const distanceData = [];
    const durationData = [];
    const paceData = [];

    const sessionCountPerDate = {};

    data.forEach(session => {
      const sessionDate = session.date;
      let isNewSession = true;

      session.entries.forEach(entry => {
        if (entry.type === "cardio") {
          if (isNewSession) {
            sessionCountPerDate[sessionDate] = (sessionCountPerDate[sessionDate] || 0) + 1;
            isNewSession = false;
          }

          const sessionIndex = sessionCountPerDate[sessionDate] || 1;
          const sessionLabel = sessionCountPerDate[sessionDate] > 1 ? ` (Session ${sessionIndex})` : '';
          const label = `${sessionDate}${sessionLabel}`;
          labels.push(label);

          const distance = entry.distance ?? 0;
          const duration = entry.duration ?? 0;
          const pace = entry.pace ?? null;

          distanceData.push(distance);
          durationData.push(duration);
          paceData.push(pace);

        }
      });
    });

    if (sessionDetailChart) sessionDetailChart.destroy();
    if (paceChart) paceChart.destroy();

    sessionDetailChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Distance (mi)",
            type: "bar",
            data: distanceData,
            backgroundColor: "rgba(59, 130, 246, 0.6)",
            borderColor: "rgba(59, 130, 246, 1)",
            borderWidth: 1,
            yAxisID: "yDistance"
          },
          {
            label: "Duration (min)",
            type: "bar",
            data: durationData,
            backgroundColor: "rgba(234, 179, 8, 0.6)",
            borderColor: "rgba(202, 138, 4, 1)",
            borderWidth: 1,
            yAxisID: "yDuration"
          }
        ]
      },
      options: {
        responsive: true,
        interaction: { mode: "index", intersect: false },
        scales: {
          x: {
            ticks: {
              autoSkip: true,
              maxRotation: 60,
              minRotation: 45,
              callback: function(value) {
                const label = this.getLabelForValue(value);
                return label.length > 30 ? label.slice(0, 30) + "…" : label;
              }
            }
          },
          yDistance: {
            type: "linear",
            position: "left",
            beginAtZero: true,
            title: { display: true, text: "Distance (mi)" }
          },
          yDuration: {
            type: "linear",
            position: "right",
            beginAtZero: true,
            grid: { drawOnChartArea: false },
            title: { display: true, text: "Duration (minutes)" }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                const value = context.parsed.y;
                const label = context.dataset.label;
                return `${label}: ${value === null || value === 0 ? "-" : value}`;
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

    // Create pace chart if any pace data is available
    const hasValidPace = paceData.some(p => p !== null);
    if (hasValidPace) {
      paceChart = new Chart(paceCtx, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "Pace (min/mile)",
              data: paceData,
              backgroundColor: "rgba(34, 197, 94, 0.2)",
              borderColor: "rgba(34, 197, 94, 1)",
              borderWidth: 2,
              spanGaps: true,
              tension: 0.3,
              pointRadius: 3,
              pointBackgroundColor: "rgba(34, 197, 94, 1)"
            }
          ]
        },
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: false,
              title: {
                display: true,
                text: "Pace (min/mile)"
              }
            }
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: function(context) {
                  return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} min/mi`;
                }
              }
            }
          }
        }
      });
    }

  } catch (err) {
    console.error("[detailedSessionsChart] Error:", err);
    container.innerHTML = "<p class='text-center text-red-500'>Failed to load chart.</p>";
  }
}
