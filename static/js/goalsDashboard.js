import { authFetch } from "./auth/authFetch.js";

document.addEventListener('DOMContentLoaded', () => {
  fetchGoalsAndRender();

  document.getElementById('applyFilters').addEventListener('click', fetchGoalsAndRender);
});

async function fetchGoalsAndRender() {
  const container = document.getElementById('goals-container');
  if (!container) return;

  container.innerHTML = 'Loading...';

  try {
    const type = document.getElementById('goalTypeFilter').value;
    const exercise = document.getElementById('exerciseTypeFilter').value;
    const activeOnly = document.getElementById('activeOnly').checked;

    const res = await authFetch(`/api/goals/with-progress`);
    const data = await res.json();

    container.innerHTML = '';

    if (!data.length) {
      container.innerHTML = '<p>No goals found.</p>';
      return;
    }

    data.forEach(goal => {
      const latestProgress = goal.progress?.[goal.progress.length - 1];
      const isGoalComplete = latestProgress?.is_complete;

      const card = document.createElement('div');
      card.className = `rounded shadow p-4 transition ${
        isGoalComplete ? 'bg-green-50 border border-green-400' : 'bg-white'
      }`;

      card.innerHTML = `
        <h2 class="text-xl font-semibold mb-1">${goal.name}</h2>
        <p class="text-sm text-gray-500 mb-1">
          ${goal.exercise_name || goal.exercise_type} • 
          <span class="italic text-xs">${goal.goal_type === 'single_session' ? 'Single Session Goal' : 'Aggregate Goal'}</span>
        </p>
        ${renderAllProgress(goal)}
        <p class="text-xs text-gray-400 mt-2">From ${goal.start_date} to ${goal.end_date || 'ongoing'}</p>
      `;

      container.appendChild(card);
    });

  } catch (err) {
    console.error('Error loading goals:', err);
    container.innerHTML = '<p class="text-red-600">Failed to load goals.</p>';
  }
}

function renderAllProgress(goal) {
  const targetsByMetric = {};
  goal.targets.forEach(t => {
    targetsByMetric[t.metric] = t.value;
  });

  const progressByMetric = {};
  goal.progress.forEach(p => {
    const m = p.metric;
    // Update only if value is greater OR it's more recent
    if (
      !progressByMetric[m] ||
      p.value_achieved > progressByMetric[m].total
    ) {
      progressByMetric[m] = {
        total: p.value_achieved,
        isComplete: p.is_complete
      };
    }
  });

  let html = "";
  for (const metric in targetsByMetric) {
    const { total = 0, isComplete = false } = progressByMetric[metric] || {};
    const target = targetsByMetric[metric];

    const useCheckbox = goal.goal_type === "single_session" || metric === "pace" || metric === "weight";

    html += useCheckbox
      ? renderCheckboxProgress({
          metric,
          total,
          target,
          units: getUnitsForMetric(metric),
          isComplete
        })
      : renderProgress({
          metric,
          total,
          target,
          units: getUnitsForMetric(metric),
          isComplete
        });
  }

  return html;
}

function renderProgress(p) {
  const percent = Math.min(100, (p.total / p.target) * 100).toFixed(0);
  const isComplete = p.total >= p.target;

  return `
    <div class="mb-2">
      <div class="flex justify-between text-sm font-medium mb-1">
        <span>${p.metric.toUpperCase()}</span>
        <span>${p.total} / ${p.target} ${p.units}</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div class="h-full ${isComplete ? 'bg-green-500' : 'bg-blue-500'}" style="width: ${percent}%"></div>
      </div>
    </div>
  `;
}

function renderCheckboxProgress(p) {
  return `
    <div class="mb-2 flex items-center space-x-2">
      <input type="checkbox" ${p.isComplete ? 'checked' : ''} disabled class="accent-green-600 h-4 w-4">
      <label class="text-sm font-medium">
        ${p.metric.toUpperCase()}: 
        ${p.metric === 'pace' ? `${p.target} ${p.units}` : `${p.total} / ${p.target} ${p.units}`}
      </label>
    </div>
  `;
}


function getUnitsForMetric(metric) {
  return {
    distance: "miles",
    duration: "min",
    weight: "lb",
    reps: "reps",
    sets: "sets",
    sessions: "sessions",
    pace: "min/mile",
  }[metric] || "";
}
