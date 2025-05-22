import { authFetch } from './authFetch.js';

const select = document.getElementById("exerciseSelect");
const trendInsight = document.getElementById("trendInsight");
const btnStrength = document.getElementById("btnStrength");
const btnCardio = document.getElementById("btnCardio");

const rmChartCanvas = document.getElementById("rmChart");
const volumeChartCanvas = document.getElementById("volumeChart");
const intensityChartCanvas = document.getElementById("intensityChart");

const startDateInput = document.getElementById("startDate");
const endDateInput = document.getElementById("endDate");

let currentType = "strength";
let rmChart, volumeChart, intensityChart;

// Load exercise list
async function loadExercises(type) {
  try {
    const res = await authFetch(`/api/exercises/${type}`);
    const exercises = await res.json();

    select.innerHTML = "";
    exercises.forEach(exercise => {
      const option = document.createElement("option");
      option.value = exercise;
      option.textContent = exercise;
      select.appendChild(option);
    });

    if (exercises.length > 0) {
      select.value = exercises[0];
      select.dispatchEvent(new Event("change"));
    } else {
      trendInsight.textContent = "No exercises available.";
    }
  } catch (err) {
    console.error("[loadExercises] Failed:", err);
    select.innerHTML = '<option disabled selected>Error loading exercises</option>';
  }
}

select.addEventListener("change", async () => {
  const exercise = select.value;
  const startDate = startDateInput.value;
  const endDate = endDateInput.value;

  // Basic input validation
  if (!exercise) {
    trendInsight.textContent = "Please select an exercise.";
    return;
  }

  if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
    trendInsight.textContent = "Start date must be before end date.";
    return;
  }

  trendInsight.textContent = "Loading trend data...";

  const params = new URLSearchParams();
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  try {
    const rmRes = await authFetch(`/api/exercise-data/1rm-trend/${encodeURIComponent(exercise)}?${params}`);
    const rmData = await rmRes.json();

    const volumeRes = await authFetch(`/api/exercise-data/volume-trend/${encodeURIComponent(exercise)}?${params}`);
    const volumeData = await volumeRes.json();

    const intensityRes = await authFetch(`/api/exercise-data/relative-intensity/${encodeURIComponent(exercise)}?${params}`);
    const intensityData = await intensityRes.json();

    renderRmChart(rmData);
    renderVolumeChart(volumeData);
    renderIntensityChart(intensityData);

    trendInsight.textContent = "";
  } catch (err) {
    console.error("[trend fetch] Failed:", err);
    trendInsight.textContent = "Error loading trend data.";
  }
});


// Refresh charts when date inputs change
[startDateInput, endDateInput].forEach(input => {
  input.addEventListener("change", () => {
    if (select.value) {
      select.dispatchEvent(new Event("change"));
    }
  });
});

// Toggle type buttons
btnStrength.addEventListener("click", () => {
  currentType = "strength";
  btnStrength.classList.add("bg-blue-600", "text-white");
  btnCardio.classList.remove("bg-blue-600", "text-white");
  btnCardio.classList.add("bg-gray-300", "text-black");
  loadExercises("strength");
});

btnCardio.addEventListener("click", () => {
  currentType = "cardio";
  btnCardio.classList.add("bg-blue-600", "text-white");
  btnStrength.classList.remove("bg-blue-600", "text-white");
  btnStrength.classList.add("bg-gray-300", "text-black");
  loadExercises("cardio");
});

// Chart renderers
function renderRmChart(data) {
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

function renderVolumeChart(data) {
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

function renderIntensityChart(data) {
  if (intensityChart) intensityChart.destroy();

  // Format labels with newline between date and set #
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
            maxRotation: 0,   // Prevent diagonal labels
            minRotation: 0,   // Keep horizontal
            autoSkip: false   // Show all labels
          }
        }
      }
    }
  });
}

// Initial load
loadExercises(currentType);
