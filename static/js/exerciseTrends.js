import { authFetch } from './authFetch.js';

const select = document.getElementById("exerciseSelect");
const trendInsight = document.getElementById("trendInsight");
const btnStrength = document.getElementById("btnStrength");
const btnCardio = document.getElementById("btnCardio");

let chart;
let currentType = "strength";

// Fetch & load exercises
async function loadExercises(type) {
  console.log(`[loadExercises] Fetching ${type} exercises...`);
  try {
    const res = await authFetch(`/api/exercises/${type}`);
    const exercises = await res.json();

    // Clear and repopulate
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

// Fetch trend data for selected exercise
async function fetchExerciseData(exercise) {
  const res = await authFetch(`/api/exercise-data/${encodeURIComponent(exercise)}`);
  const data = await res.json();
  return data;
}

// Generate simple trend insight based on primary metric
function generateTrendLine(data) {
  if (data.length < 2) return "Insufficient data";

  let primaryMetric;
  if (currentType === "strength") {
    primaryMetric = "weight"; // Or "reps", or compare both
  } else {
    primaryMetric = "distance"; // or "duration_minutes"
  }

  const values = data.map(d => d[primaryMetric]).filter(v => v != null);
  if (values.length < 2) return "Insufficient trend data";

  const slope = (values.at(-1) - values[0]) / values.length;
  if (slope > 5) return "Consistent growth";
  else if (slope > 0) return "Moderate growth";
  return "Trend appears flat or declining";
}

// Render the chart
function renderChart(data) {
  const ctx = document.getElementById("trendChart").getContext("2d");
  const labels = data.map(d => d.date);

  let datasets = [];

  if (currentType === "strength") {
    datasets = [
      {
        label: "Reps",
        data: data.map(d => d.reps),
        borderColor: "rgb(75, 192, 192)",
        fill: false,
        tension: 0.3
      },
      {
        label: "Weight",
        data: data.map(d => d.weight),
        borderColor: "rgb(255, 99, 132)",
        fill: false,
        tension: 0.3
      },
      {
        label: "Sets",
        data: data.map(d => d.sets),
        borderColor: "rgb(54, 162, 235)",
        fill: false,
        tension: 0.3
      }
    ];
  } else {
    datasets = [
      {
        label: "Distance (km/mi)",
        data: data.map(d => d.distance),
        borderColor: "rgb(153, 102, 255)",
        fill: false,
        tension: 0.3
      },
      {
        label: "Duration (min)",
        data: data.map(d => d.duration_minutes),
        borderColor: "rgb(255, 159, 64)",
        fill: false,
        tension: 0.3
      }
    ];
  }

  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets
    },
    options: {
      scales: {
        x: {
          title: { display: true, text: "Date" }
        },
        y: {
          title: {
            display: true,
            text: currentType === "strength" ? "Reps / Weight / Sets" : "Distance / Duration"
          }
        }
      }
    }
  });
}

// Handle dropdown change
select.addEventListener("change", async () => {
  const exercise = select.value;
  const raw = await fetchExerciseData(exercise);
  const trend = generateTrendLine(raw);
  trendInsight.textContent = trend;
  renderChart(raw);
});

// Toggle between strength/cardio
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

// Load initial
loadExercises(currentType);
