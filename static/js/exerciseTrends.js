import { authFetch } from './authFetch.js';

const select = document.getElementById("exerciseSelect");
const trendInsight = document.getElementById("trendInsight");
const btnStrength = document.getElementById("btnStrength");
const btnCardio = document.getElementById("btnCardio");

const rmChartCanvas = document.getElementById("rmChart");
const volumeChartCanvas = document.getElementById("volumeChart");

let currentType = "strength";
let rmChart, volumeChart;

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

// Handle dropdown change
select.addEventListener("change", async () => {
  const exercise = select.value;
  trendInsight.textContent = "Loading trend data...";

  try {
    // 1RM Trend API
    const rmRes = await authFetch(`/api/exercise-data/1rm-trend/${encodeURIComponent(exercise)}`);
    const rmData = await rmRes.json();

    // Volume Trend API
    const volumeRes = await authFetch(`/api/exercise-data/volume-trend/${encodeURIComponent(exercise)}`);
    const volumeData = await volumeRes.json();

    renderRmChart(rmData);
    renderVolumeChart(volumeData);

    trendInsight.textContent = "";
  } catch (err) {
    console.error("[trend fetch] Failed:", err);
    trendInsight.textContent = "Error loading trend data.";
  }
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


// Initial load
loadExercises(currentType);
