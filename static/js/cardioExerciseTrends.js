import { authFetch } from './auth/authFetch.js';
import { renderSessionTable } from "./tables/sessionTable.js";
import { renderCardioDetailedSessionsChart } from "./charts/cardio/cardioDetailedSessionsChart.js";
import { renderCardioPrCharts } from "./charts/cardio/renderCardioPrCharts.js";
import { renderCardioAiInsights, showLoadingCardioAiInsights } from "./charts/cardio/cardioAiInsights.js";
import {renderGoalCard} from "./goalCard.js";

// DOM elements
const select = document.getElementById("exerciseSelect");
const startDateInput = document.getElementById("startDate");
const endDateInput = document.getElementById("endDate");

// Track the latest request
let currentRequestId = 0;

// Load only cardio exercises
async function loadExercises() {
  try {
    const res = await authFetch(`/api/exercises/cardio`);
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

  // Increment the request ID to invalidate older requests
  const requestId = ++currentRequestId;

  try {
    const prRes = await authFetch(`/api/personal-records/by-exercise/${encodeURIComponent(exercise)}?${params}`);
    const prData = await prRes.json();

    if (requestId !== currentRequestId) return; // Cancel if outdated

    if (prData.success) {
      const latestPRs = prData.personal_records.filter(pr => pr.is_latest);
      const highlightContainer = document.getElementById("latestPrHighlight");
      highlightContainer.innerHTML = ""; // Clear previous content

      if (latestPRs.length > 0) {
        latestPRs.forEach(pr => {
          const card = document.createElement("div");
          card.className = "bg-white shadow-md rounded-lg p-4 mb-3 border-l-4 border-green-500";

          const fieldName = pr.field.toUpperCase();
          const dateStr = new Date(pr.datetime).toLocaleDateString();

          let valueDisplay;
          if (pr.field === 'pace' && pr.units === 'min/mi') {
            const minutes = Math.floor(pr.value);
            const seconds = Math.floor((pr.value - minutes) * 60);
            const secondsStr = seconds.toString().padStart(2, '0');
            valueDisplay = `${minutes}:${secondsStr} ${pr.units}`;
          } else {
            valueDisplay = `${pr.value} ${pr.units}`;
          }

          card.innerHTML = `
            <div class="text-lg font-semibold text-gray-800">🏅 ${fieldName}</div>
            <div class="text-gray-600 text-sm">${valueDisplay}</div>
            <div class="text-gray-500 text-xs">Set on ${dateStr}</div>
          `;

          highlightContainer.appendChild(card);
        });
      } else {
        highlightContainer.innerHTML = `<div class="text-gray-500 italic">No records found.</div>`;
      }

      renderCardioPrCharts(prData.personal_records);
    }

    await renderSessionTable(exercise, startDate, endDate);
    await renderCardioDetailedSessionsChart(exercise, startDate, endDate);

    // Fetch and render Exercise Goals using renderGoalCard
    const goalsSection = document.getElementById("exerciseGoalsContainer");
    goalsSection.innerHTML = "";

    try {
      const goalsRes = await authFetch(`/api/goals/with-progress?exercise=${encodeURIComponent(exercise)}`);
      const goalsData = await goalsRes.json();

      if (goalsData.length === 0) {
        goalsSection.innerHTML = `<div class="text-gray-500 italic">No active goals for this exercise.</div>`;
      } else {
        goalsData.forEach(goal => {
          const goalHTML = renderGoalCard(goal, { showDelete: false });
          goalsSection.insertAdjacentHTML("beforeend", goalHTML);
        });
      }
    } catch (err) {
      console.error("[loadExerciseGoals] Failed:", err);
      goalsSection.innerHTML = `<div class="text-red-500">Failed to load goals.</div>`;
    }

    // ✅ AI insights for cardio
    showLoadingCardioAiInsights();
    const aiRes = await authFetch(`/api/exercise-data/cardio/ai-insights/${encodeURIComponent(exercise)}?${params}`);
    const aiData = await aiRes.json();

    if (requestId !== currentRequestId) return; // Cancel if outdated
    renderCardioAiInsights(aiData);

  } catch (err) {
    if (requestId === currentRequestId) {
      console.error("[trend fetch] Failed:", err);
    }
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