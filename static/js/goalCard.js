export function renderGoalCard(goal, options = {}) {
  const { showDelete = false } = options;

  // Determine goal status styling
  let cardClasses = 'rounded shadow p-4 transition ';
  if (goal.is_complete) {
    cardClasses += 'bg-green-50 border border-green-400';
  } else if (goal.is_expired) {
    cardClasses += 'bg-red-50 border border-red-400';
  } else {
    cardClasses += 'bg-white';
  }

  // Delete button HTML if enabled
  const deleteBtnHTML = showDelete
    ? `<button class="text-gray-400 hover:text-gray-600 text-xl font-bold ml-4 delete-goal-btn" data-goal-id="${goal.id}" title="Delete Goal">×</button>`
    : '';

  return `
    <div class="${cardClasses}">
      <div class="flex justify-between items-start">
        <div>
          <h2 class="text-xl font-semibold mb-1">${goal.name}</h2>
          <p class="text-sm text-gray-500 mb-1">
            ${goal.exercise_name || goal.exercise_type} • 
            <span class="italic text-xs">${goal.goal_type === 'single_session' ? 'Single Session Goal' : 'Aggregate Goal'}</span>
          </p>
          ${renderAllProgress(goal)}
          <p class="text-xs text-gray-400 mt-2">
            From ${goal.start_date} to ${goal.end_date || 'ongoing'}
          </p>
        </div>
        ${deleteBtnHTML}
      </div>
    </div>
  `;
}



function renderAllProgress(goal) {
  const targetsByMetric = {};
  goal.targets.forEach(t => targetsByMetric[t.metric] = t.value);

  const progressByMetric = {};
  goal.progress.forEach(p => {
    const m = p.metric;
    if (!progressByMetric[m] || p.value_achieved > progressByMetric[m].total) {
      progressByMetric[m] = { total: p.value_achieved };
    }
  });

  let html = "";
  for (const metric in targetsByMetric) {
    const { total = 0 } = progressByMetric[metric] || {};
    const target = targetsByMetric[metric];

    const useCheckbox = goal.goal_type === "single_session" || metric === "pace" || metric === "weight";
    const isComplete = total >= target;

    html += useCheckbox
      ? renderCheckboxProgress({ metric, total, target, units: getUnitsForMetric(metric), isComplete })
      : renderProgress({ metric, total, target, units: getUnitsForMetric(metric), isComplete });
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
