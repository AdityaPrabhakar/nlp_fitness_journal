import { showPRToast } from './toast.js';
import { openModal, setupModalTriggers } from './modal.js';
import { renderTrendCharts } from './renderTrendCharts.js';
import { authFetch } from './auth/authFetch.js';

document.addEventListener('DOMContentLoaded', () => {
  setupModalTriggers();
  const logForm = document.getElementById('logForm');
  if (!logForm) return;

  logForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const entryText = document.getElementById('entryText').value.trim();
    if (!entryText) return;

    try {
      const response = await authFetch('/api/log-workout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entry: entryText })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        document.getElementById('entryText').value = '';

        if (result.new_prs?.length) {
          showPRToast(result.new_prs);
        }

        const sessionId = result.session_id;
        const sessionDate = result.session_date;

        const trendUrl = `/api/workout-trends/${sessionId}?date=${encodeURIComponent(sessionDate)}&count=5`;
        const trendRes = await authFetch(trendUrl);
        const trendData = await trendRes.json();

        const modalContent = `
          <div class="p-4 space-y-6">
            <h2 class="text-2xl font-bold text-center">Journal Entry Created! 🥳</h2>
            <p class="text-gray-600 text-lg text-center">Workout Summary</p>
            <div id="trend-tabs" class="mb-4 flex space-x-2 border-b"></div>
            <div id="trend-container" class="mt-4"></div>
          </div>
        `;

        openModal(modalContent, { title: 'Workout Summary', size: 'xl' });

        setTimeout(() => renderTrendCharts(trendData), 100);
      } else {
        alert("Error logging workout: " + (result.error || "Unknown error"));
      }
    } catch (err) {
      console.error("Log form error:", err);
      alert("Failed to log workout.");
    }
  });
});
