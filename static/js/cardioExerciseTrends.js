import { authFetch } from './auth/authFetch.js';
import { renderSessionTable } from "./tables/sessionTable.js";
import { renderDetailedSessionsChart } from "./charts/strength/strengthDetailedSessionsChart.js";

const select = document.getElementById("exerciseSelect");
const startDateInput = document.getElementById("startDate");
const endDateInput = document.getElementById("endDate");

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

  try {
    const prRes = await authFetch(`/api/personal-records/by-exercise/${encodeURIComponent(exercise)}?${params}`);
    const prData = await prRes.json();

    if (prData.success) {
      const latest = prData.personal_records.find(pr => pr.is_latest);
      if (latest) {
        document.getElementById("latestPrHighlight").textContent = `${latest.value} ${latest.units} on ${new Date(latest.datetime).toLocaleDateString()}`;
      } else {
        document.getElementById("latestPrHighlight").textContent = "No records found.";
      }
    } else {
      console.error("Failed to load PR data:", prData.error);
      document.getElementById("latestPrHighlight").textContent = "Error loading PR data.";
    }

    await renderSessionTable(exercise, startDate, endDate);
    await renderDetailedSessionsChart(exercise, startDate, endDate);

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
