import { authFetch } from './authFetch.js';

const select = document.getElementById("exerciseSelect");
const trendInsight = document.getElementById("trendInsight");
const btnStrength = document.getElementById("btnStrength");
const btnCardio = document.getElementById("btnCardio");

let chart;
let currentType = "strength";

// Load exercise list
async function loadExercises(type) {
  console.log(`[loadExercises] Fetching ${type} exercises...`);
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

// Fetch raw entry data
async function fetchExerciseData(exercise) {
  const res = await authFetch(`/api/exercise-data/${encodeURIComponent(exercise)}`);
  const data = await res.json();
  return data;
}

// Compute adaptive "Effort Score"
function computeEffortScore(entry) {
  const reps = entry.reps ?? 1;
  const sets = entry.sets ?? 1;
  const weight = entry.weight;

  if (weight != null && reps != null && sets != null) {
    return weight * reps * sets;
  }
  if (weight != null && reps != null) {
    return weight * reps;
  }
  if (reps != null && sets != null) {
    return reps * sets;
  }
  if (reps != null) return reps;
  if (weight != null) return weight;

  return 0; // fallback
}

// Render chart
function renderChart(data) {
  const ctx = document.getElementById("trendChart").getContext("2d");
  const labels = data.map(d => d.date);

  const values = data.map(d =>
    currentType === "strength"
      ? computeEffortScore(d)
      : d.distance ?? d.duration_minutes ?? 0
  );

  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: currentType === "strength" ? "Effort Score" : "Distance / Duration",
        data: values,
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.3
      }]
    },
    options: {
      scales: {
        x: { title: { display: true, text: "Date" }},
        y: { title: { display: true, text: currentType === "strength" ? "Effort Score" : "Distance" }}
      }
    }
  });
}

// Generate adaptive trend insight
function generateTrendLine(data) {
  const values = data.map(d =>
    currentType === "strength"
      ? computeEffortScore(d)
      : d.distance ?? d.duration_minutes ?? 0
  );

  if (values.length < 2) return "Insufficient data";

  const slope = (values.at(-1) - values[0]) / values.length;
  if (slope > 10) return "Strong growth";
  else if (slope > 2) return "Moderate growth";
  else if (slope > 0) return "Slight growth";
  return "Trend appears flat or declining";
}

// Handle dropdown change
select.addEventListener("change", async () => {
  const exercise = select.value;
  const raw = await fetchExerciseData(exercise);
  const trend = generateTrendLine(raw);
  trendInsight.textContent = trend;
  renderChart(raw);
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

// Load default on page load
loadExercises(currentType);
