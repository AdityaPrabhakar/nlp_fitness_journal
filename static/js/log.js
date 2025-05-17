// static/js/log.js
import { showPRToast } from './toast.js';
import { openModal, setupModalTriggers } from './modal.js';
import { renderSessionDetails } from './sessionRenderer.js';

document.addEventListener('DOMContentLoaded', () => {
  setupModalTriggers();
  const logForm = document.getElementById('logForm');
  if (!logForm) return;

  logForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const entryText = document.getElementById('entryText').value.trim();
    if (!entryText) return;

    try {
      const response = await fetch('/api/log-workout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ entry: entryText })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        document.getElementById('entryText').value = '';

        if (result.new_prs?.length) {
          showPRToast(result.new_prs);
        }

        const sessionId = result.session_id;
        const sessionRes = await fetch(`/api/session/${sessionId}`);
        const sessionData = await sessionRes.json();

        const content = `
          <div class="max-h-[80vh] overflow-y-auto pr-2">
            <div class="bg-white p-4 shadow rounded-lg border">
              ${renderSessionDetails(sessionData)}
            </div>
          </div>
        `;

        openModal(content, { title: 'Workout Session Insights', size: 'xl' });

      } else {
        alert("Error logging workout: " + (result.error || "Unknown error"));
      }
    } catch (err) {
      console.error("Log form error:", err);
      alert("Failed to log workout.");
    }
  });
});
