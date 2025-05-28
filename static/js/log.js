import { openModal, setupModalTriggers } from './modal.js';
import { renderTrendCharts } from './renderTrendCharts.js';
import { authFetch } from './auth/authFetch.js';

function showLoadingWorkoutSummary() {
  console.log('[Modal] Showing loading workout summary modal...');
  const modalContent = `
    <div class="p-6 text-center space-y-4">
      <svg class="animate-spin h-6 w-6 mx-auto text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
      </svg>
      <p class="text-gray-700 text-sm">Creating entry and generating session data...</p>
    </div>
  `;
  openModal(modalContent, { title: 'Logging Workout...', size: 'xl' });
}

document.addEventListener('DOMContentLoaded', () => {
  console.log('[Init] DOM fully loaded, setting up modal triggers...');
  setupModalTriggers();

  const logForm = document.getElementById('logForm');
  if (!logForm) {
    console.warn('[Form] #logForm not found on page.');
    return;
  }

  logForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log('[Form] Log form submitted.');

    const entryText = document.getElementById('entryText').value.trim();
    if (!entryText) {
      console.warn('[Form] entryText is empty, aborting.');
      return;
    }

    showLoadingWorkoutSummary();

    try {
      console.log('[API] Sending POST to /api/log-workout...');
      const response = await authFetch('/api/log-workout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entry: entryText })
      });

      const result = await response.json();
      console.log('[API] Received response from /api/log-workout:', result);

      if (response.ok && result.success) {
        document.getElementById('entryText').value = '';
        console.log('[Workout] Entry logged successfully.');

        if (
          !result.session_id &&
          (!result.goals || result.goals.length === 0) &&
          (!result.repeated_goals || result.repeated_goals.length === 0)
        ) {
          const modalContent = `
            <div class="p-4 space-y-6 text-center">
              <h2 class="text-2xl font-bold">No Workout Logged</h2>
              <p class="text-gray-600 text-lg">No workout session or goals were created. Please make sure your entry includes valid workout or goal details.</p>
            </div>
          `;
          openModal(modalContent, { title: 'No Entry Detected', size: 'md' });
          return;
        }

        const sessionId = result.session_id;
        const sessionDate = result.session_date;
        console.log(`[Session] ID: ${sessionId}, Date: ${sessionDate}`);

        const prHtml = result.new_prs?.length
          ? `
            <div class="bg-green-50 border border-green-200 text-green-900 rounded-lg p-4 transition-all duration-500 ease-out">
              <h3 class="font-semibold text-lg mb-2 flex items-center gap-2">
                <span>🎉 New Personal Records!</span>
              </h3>
              <ul class="list-disc list-inside space-y-1">
                ${result.new_prs.map(pr => `
                  <li><strong>${pr.exercise}</strong> (${pr.field}): ${pr.value} ${pr.units}</li>
                `).join('')}
              </ul>
            </div>
          `
          : '';

        const goalsHtml = result.goals?.length
          ? `
            <div class="bg-blue-50 border border-blue-200 text-blue-900 rounded-lg p-4 transition-all duration-500 ease-out">
              <h3 class="font-semibold text-lg mb-2 flex items-center gap-2">
                <span>🎯 New Goals Logged</span>
              </h3>
              <ul class="space-y-3">
                ${result.goals.map(goal => `
                  <li class="flex items-start gap-2">
                    <span class="text-xl">🎯</span>
                    <div>
                      <div class="font-semibold">${goal.exercise_name || goal.name}</div>
                      ${goal.description ? `<div class="text-sm text-gray-700">${goal.description}</div>` : ''}
                      ${goal.goal_type ? `<div class="text-sm text-gray-600 mt-1">Type: ${goal.goal_type}</div>` : ''}
                      ${goal.targets?.length ? `
                        <ul class="ml-4 mt-1 list-disc list-inside text-sm text-blue-900 space-y-1">
                          ${goal.targets.map(t => `<li>${t.target_metric}: ${t.target_value}</li>`).join('')}
                        </ul>
                      ` : ''}
                      ${goal.end_date ? `
                        <div class="text-xs text-gray-500 mt-1">Ends: ${goal.end_date}</div>
                      ` : ''}
                    </div>
                  </li>
                `).join('')}
              </ul>
              ${
                result.repeated_goals?.length
                  ? `<p class="mt-4 text-sm text-gray-600 italic">⚠️ ${result.repeated_goals.length} goal(s) were already logged and skipped.</p>`
                  : ''
              }
            </div>
          `
          : result.repeated_goals?.length
            ? `
              <div class="bg-yellow-50 border border-yellow-200 text-yellow-900 rounded-lg p-4 transition-all duration-500 ease-out">
                <h3 class="font-semibold text-lg mb-2 flex items-center gap-2">
                  <span>⚠️ Repeated Goals Skipped</span>
                </h3>
                <ul class="space-y-3">
                  ${result.repeated_goals.map(goal => `
                    <li class="flex items-start gap-2">
                      <span class="text-xl">🎯</span>
                      <div>
                        <div class="font-semibold">${goal.exercise_name || goal.name}</div>
                        ${goal.description ? `<div class="text-sm text-gray-700">${goal.description}</div>` : ''}
                        ${goal.goal_type ? `<div class="text-sm text-gray-600 mt-1">Type: ${goal.goal_type}</div>` : ''}
                        ${goal.targets?.length ? `
                          <ul class="ml-4 mt-1 list-disc list-inside text-sm text-yellow-900 space-y-1">
                            ${goal.targets.map(t => `<li>${t.target_metric}: ${t.target_value}</li>`).join('')}
                          </ul>
                        ` : ''}
                        ${goal.end_date ? `
                          <div class="text-xs text-gray-500 mt-1">Ends: ${goal.end_date}</div>
                        ` : ''}
                      </div>
                    </li>
                  `).join('')}
                </ul>
              </div>
            `
            : '';

        let trendData = null;
        if (sessionId) {
          const trendUrl = `/api/workout-trends/${sessionId}?date=${encodeURIComponent(sessionDate)}&count=5`;
          console.log('[API] Fetching workout trend data from:', trendUrl);
          const trendRes = await authFetch(trendUrl);
          trendData = await trendRes.json();
          console.log('[API] Received trend data:', trendData);
        }

        const modalContent = `
          <div class="p-4 space-y-6">
            <h2 class="text-2xl font-bold text-center">Journal Entry Created! 🥳</h2>
            ${prHtml}
            ${goalsHtml}
            ${
              sessionId
                ? `
                <p class="text-gray-600 text-lg text-center">Workout Summary</p>
                <div id="trend-tabs" class="mb-4 flex space-x-2 border-b"></div>
                <div id="trend-container" class="mt-4"></div>
                `
                : ''
            }
          </div>
        `;

        console.log('[Modal] Replacing loading modal with summary modal...');
        openModal(modalContent, { title: 'Workout Summary', size: 'xl' });

        if (trendData) {
          setTimeout(() => {
            console.log('[Chart] Rendering trend charts...');
            renderTrendCharts(trendData);
          }, 100);
        }
      } else {
        console.error('[Error] Workout log failed:', result.error);
        alert("Error logging workout: " + (result.error || "Unknown error"));
      }
    } catch (err) {
      console.error("[Exception] Log form error:", err);
      alert("Failed to log workout. Please ensure your input contains valid workout entries.");
    }
  });
});
