import { authFetch } from './auth/authFetch.js';
import {renderRmChart} from "./charts/rmChart.js";
import {renderVolumeChart} from "./charts/volumeChart.js";
import {renderIntensityChart} from "./charts/intensityChart.js";
import {renderSessionTable} from "./tables/sessionTable.js";

const select = document.getElementById("exerciseSelect");
const trendInsight = document.getElementById("trendInsight");
const btnStrength = document.getElementById("btnStrength");
const btnCardio = document.getElementById("btnCardio");

const startDateInput = document.getElementById("startDate");
const endDateInput = document.getElementById("endDate");

let currentType = "strength";

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

// Main change handler
select.addEventListener("change", async () => {
  const exercise = select.value;
  const startDate = startDateInput.value;
  const endDate = endDateInput.value;

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

    await renderSessionTable(exercise, startDate, endDate);

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


// Initial load
loadExercises(currentType);
