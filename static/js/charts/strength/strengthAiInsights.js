export function showLoadingAiInsights() {
  const container = document.getElementById("aiInsightsContainer");
  container.innerHTML = `
    <div class="flex items-center space-x-2 text-sm text-gray-600">
      <svg class="animate-spin h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
      </svg>
      <span>Analyzing your strength sessions...</span>
    </div>
  `;
}

export function renderAiInsights(data) {
  const container = document.getElementById("aiInsightsContainer");
  container.innerHTML = "";

  if (
    !data ||
    !data.recommended_sets ||
    !Array.isArray(data.recommended_sets) ||
    data.recommended_sets.length === 0 ||
    !data.rationale
  ) {
    container.innerHTML = `<p class="text-sm text-red-600">AI insights not available for this exercise.</p>`;
    return;
  }

  const rationale = data.rationale;
  const setsHtml = data.recommended_sets
    .map((set) => {
      return `
        <div class="flex items-center space-x-2 text-sm text-gray-800 font-medium">
          <span class="bg-gray-100 text-gray-800 px-2 py-1 rounded">Set ${set.set_number}:</span>
          <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-xl">Reps: ${set.reps}</span>
          ${
            set.weight !== undefined && set.weight !== null
              ? `<span class="bg-green-100 text-green-800 px-3 py-1 rounded-xl">Weight: ${set.weight} lbs</span>`
              : ""
          }
        </div>
      `;
    })
    .join("");

  container.innerHTML = `
    <div class="mb-4">
      <h3 class="text-lg font-semibold text-gray-800 mb-1">🎯 Suggested Progression Scheme</h3>
      <p class="text-gray-700 text-sm mb-2">Try aiming for the following:</p>
      <div class="space-y-2 mb-4">
        ${setsHtml}
      </div>
    </div>
    <div>
      <h4 class="text-sm font-semibold text-gray-700 mb-1">💡 Why this scheme?</h4>
      <p class="text-sm text-gray-600 italic">${rationale}</p>
    </div>
  `;
}
