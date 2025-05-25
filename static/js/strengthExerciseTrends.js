import { authFetch } from './auth/authFetch.js';
import { renderRmChart } from "./charts/strength/strengthRmChart.js";
import { renderVolumeChart } from "./charts/strength/strengthVolumeChart.js";
import { renderIntensityChart } from "./charts/strength/strengthIntensityChart.js";
import { renderSessionTable } from "./tables/sessionTable.js";
import { renderStrengthDetailedSessionsChart } from "./charts/strength/strengthDetailedSessionsChart.js";
import { renderStrengthPrChart } from "./charts/strength/renderStrengthPrChart.js";
import { renderAiInsights, showLoadingAiInsights } from "./charts/strength/strengthAiInsights.js";

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
      renderStrengthPrChart(prData.personal_records);

      const latestPRs = prData.personal_records.filter(pr => pr.is_latest);
      const highlightContainer = document.getElementById("latestPrHighlight");
      highlightContainer.innerHTML = ""; // Clear previous content

      if (latestPRs.length > 0) {
        latestPRs.forEach(pr => {
          const card = document.createElement("div");
          card.className = "bg-white shadow-md rounded-lg p-4 mb-3 border-l-4 border-blue-500";

          const fieldName = pr.field.toUpperCase();
          const dateStr = new Date(pr.datetime).toLocaleDateString();
          const valueDisplay = `${pr.value} ${pr.units}`;

          card.innerHTML = `
            <div class="text-lg font-semibold text-gray-800">🏋️ ${fieldName}</div>
            <div class="text-gray-600 text-sm">${valueDisplay}</div>
            <div class="text-gray-500 text-xs">Set on ${dateStr}</div>
          `;

          highlightContainer.appendChild(card);
        });
      } else {
        highlightContainer.innerHTML = `<div class="text-gray-500 italic">No records found.</div>`;
      }
    } else {
      console.error("Failed to load PR data:", prData.error);
      document.getElementById("latestPrHighlight").textContent = "Error loading PR data.";
    }

    await renderSessionTable(exercise, startDate, endDate);
    await renderStrengthDetailedSessionsChart(exercise, startDate, endDate);

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
