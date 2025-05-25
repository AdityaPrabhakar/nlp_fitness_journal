import { authFetch } from './auth/authFetch.js';
import { renderRmChart } from "./charts/rmChart.js";
import { renderVolumeChart } from "./charts/volumeChart.js";
import { renderIntensityChart } from "./charts/intensityChart.js";
import { renderSessionTable } from "./tables/sessionTable.js";
import { renderDetailedSessionsChart } from "./charts/detailedSessionsChart.js";
import { renderPrChart } from "./charts/renderPrChart.js";
import { renderAiInsights, showLoadingAiInsights } from "./charts/aiInsights.js";

const select = document.getElementById("exerciseSelect");
const startDateInput = document.getElementById("startDate");
const endDateInput = document.getElementById("endDate");

// Load only strength exercises
async function loadExercises() {
  try {
    const res = await authFetch(`/api/exercises/strength`);
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
    }
  } catch (err) {
    console.error("[loadExercises] Failed:", err);
    select.innerHTML = '<option disabled selected>Error loading exercises</option>';
  }
}

// Handle exercise selection
select.addEventListener("change", async () => {
  const exercise = select.value;
  const startDate = startDateInput.value;
  const endDate = endDateInput.value;

  if (!exercise || (startDate && endDate && new Date(startDate) > new Date(endDate))) {
    return;
  }

  const params = new URLSearchParams();
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  try {
    const rmRes = await authFetch(`/api/exercise-data/strength/1rm-trend/${encodeURIComponent(exercise)}?${params}`);
    const rmData = await rmRes.json();

    const volumeRes = await authFetch(`/api/exercise-data/strength/volume-trend/${encodeURIComponent(exercise)}?${params}`);
    const volumeData = await volumeRes.json();

    const intensityRes = await authFetch(`/api/exercise-data/strength/relative-intensity/${encodeURIComponent(exercise)}?${params}`);
    const intensityData = await intensityRes.json();

    const prRes = await authFetch(`/api/personal-records/by-exercise/${encodeURIComponent(exercise)}?${params}`);
    const prData = await prRes.json();

    renderRmChart(rmData);
    renderVolumeChart(volumeData);
    renderIntensityChart(intensityData);

    if (prData.success) {
      renderPrChart(prData.personal_records);

      const latest = prData.personal_records.find(pr => pr.is_latest);
      if (latest) {
        document.getElementById("latestPrHighlight").textContent = `${latest.value} (${latest.field}) on ${new Date(latest.datetime).toLocaleDateString()}`;
      } else {
        document.getElementById("latestPrHighlight").textContent = "No records found.";
      }
    } else {
      console.error("Failed to load PR data:", prData.error);
      document.getElementById("latestPrHighlight").textContent = "Error loading PR data.";
    }

    await renderSessionTable(exercise, startDate, endDate);
    await renderDetailedSessionsChart(exercise, startDate, endDate);

    // AI insights
    showLoadingAiInsights();
    const aiRes = await authFetch(`/api/exercise-data/strength/ai-insights/${encodeURIComponent(exercise)}?${params}`);
    const aiData = await aiRes.json();
    renderAiInsights(aiData);

  } catch (err) {
    console.error("[trend fetch] Failed:", err);
  }
});

// Reload on date change
[startDateInput, endDateInput].forEach(input => {
  input.addEventListener("change", () => {
    if (select.value) {
      select.dispatchEvent(new Event("change"));
    }
  });
});

// Initial load
loadExercises();
