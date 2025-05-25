export function showLoadingCardioAiInsights() {
  const container = document.getElementById("aiInsightsCardio");
  container.innerHTML = `
    <div class="flex items-center space-x-2 text-sm text-gray-600">
      <svg class="animate-spin h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
      </svg>
      <span>Analyzing your cardio sessions...</span>
    </div>
  `;
}


export function renderCardioAiInsights(data) {
  const container = document.getElementById("aiInsightsCardio");
  container.innerHTML = "";

  if (!data || !Array.isArray(data.recommendations) || data.recommendations.length === 0) {
    container.innerHTML = `<p class="text-sm text-red-600">AI insights not available for this cardio exercise.</p>`;
    return;
  }

  let insightsHTML = `
    <div class="mb-4">
      <h3 class="text-lg font-semibold text-gray-800 mb-1">🏃‍♂️ Suggested Improvements</h3>
      <p class="text-gray-700 text-sm mb-2">Here’s how you can progress in your next sessions, one step at a time:</p>
      <div class="space-y-4">
  `;

  data.recommendations.forEach((rec) => {
    const { improved_metric, recommended_session, rationale } = rec;

    let pill = "";
    if (improved_metric === "distance" && recommended_session.distance_miles) {
      pill = `<span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-xl">Distance: ${recommended_session.distance_miles.toFixed(2)} miles</span>`;
    } else if (improved_metric === "duration" && recommended_session.duration_minutes) {
      pill = `<span class="bg-green-100 text-green-800 px-3 py-1 rounded-xl">Duration: ${recommended_session.duration_minutes} min</span>`;
    } else if (improved_metric === "pace" && recommended_session.target_pace_min_per_mile) {
      pill = `<span class="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-xl">Target Pace: ${recommended_session.target_pace_min_per_mile} min/mile</span>`;
    }

    insightsHTML += `
      <div>
        <div class="flex items-center space-x-2 text-sm text-gray-800 font-medium mb-1">
          ${pill}
        </div>
        <p class="text-sm text-gray-600 italic">${rationale}</p>
      </div>
    `;
  });

  insightsHTML += `</div></div>`;

  container.innerHTML = insightsHTML;
}
