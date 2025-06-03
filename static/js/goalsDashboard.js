import { authFetch } from "./auth/authFetch.js";

document.addEventListener('DOMContentLoaded', () => {
  fetchGoalsAndRender();

  document.getElementById('applyFilters').addEventListener('click', fetchGoalsAndRender);

  const dropdownBtn = document.getElementById('statusDropdownBtn');
  const dropdownMenu = document.getElementById('statusDropdown');
  dropdownBtn.addEventListener('click', () => {
    dropdownMenu.classList.toggle('hidden');
  });

  document.addEventListener('click', (e) => {
    if (!dropdownBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
      dropdownMenu.classList.add('hidden');
    }
  });
});

async function fetchGoalsAndRender() {
  const container = document.getElementById('goals-container');
  if (!container) return;

  container.innerHTML = 'Loading...';

  try {
    const type = document.getElementById('goalTypeFilter').value;
    const exercise = document.getElementById('exerciseTypeFilter').value;
    const nameSearch = document.getElementById('exerciseNameFilter').value.toLowerCase();
    const startDate = document.getElementById('startDateFilter').value;
    const endDate = document.getElementById('endDateFilter').value;
    const statusCheckboxes = document.querySelectorAll('.statusOption:checked');
    const statusFilters = Array.from(statusCheckboxes).map(cb => cb.value); // ['in_progress', 'completed']

    const res = await authFetch(`/api/goals/with-progress`);
    const data = await res.json();

    container.innerHTML = '';

    const filtered = data.filter(goal => {
      if (type && goal.goal_type !== type) return false;
      if (exercise && goal.exercise_type !== exercise) return false;
      if (nameSearch && !(goal.exercise_name || '').toLowerCase().includes(nameSearch)) return false;
      if (startDate && goal.start_date < startDate) return false;

      if (endDate) {
        if (goal.end_date && goal.end_date > endDate) return false;
        if (!goal.end_date) return false;
      }

      let status;
      if (goal.is_complete) {
        status = 'completed';
      } else if (goal.is_expired) {
        status = 'expired';
      } else {
        status = 'in_progress';
      }

      if (!statusFilters.includes(status)) return false;


      return true;
    });

    if (!filtered.length) {
      container.innerHTML = '<p>No goals found.</p>';
      return;
    }

    filtered.forEach(goal => {
      const isGoalComplete = goal.is_complete;
      const isGoalExpired = goal.is_expired;

      let cardClasses = 'rounded shadow p-4 transition ';
      if (isGoalComplete) {
        cardClasses += 'bg-green-50 border border-green-400';
      } else if (isGoalExpired) {
        cardClasses += 'bg-red-50 border border-red-400';
      } else {
        cardClasses += 'bg-white';
      }

      const card = document.createElement('div');
      card.className = cardClasses;

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
    if (
      !progressByMetric[m] ||
      p.value_achieved > progressByMetric[m].total
    ) {
      progressByMetric[m] = {
        total: p.value_achieved
      };
    }
  });

  let html = "";
  for (const metric in targetsByMetric) {
    const { total = 0 } = progressByMetric[metric] || {};
    const target = targetsByMetric[metric];

    const useCheckbox = goal.goal_type === "single_session" || metric === "pace" || metric === "weight";
    const isComplete = total >= target;

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
  return `
    <div class="mb-2">
      <div class="flex justify-between text-sm font-medium mb-1">
        <span>${p.metric.toUpperCase()}</span>
        <span>${p.total} / ${p.target} ${p.units}</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div class="h-full ${p.isComplete ? 'bg-green-500' : 'bg-blue-500'}" style="width: ${percent}%"></div>
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
