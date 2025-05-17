// static/js/log.js
import { showPRToast } from './toast.js';
import { openModal, setupModalTriggers } from './modal.js';

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

        // Optional: Fetch session if needed later
        // const sessionId = result.session_id;
        // const sessionRes = await fetch(`/api/session/${sessionId}`);
        // const sessionData = await sessionRes.json();

        // Build modal content
        const content = `
          <div class="text-center p-4">
            <h2 class="text-2xl font-bold mb-2">Journal Entry Created!</h2>
            <p class="text-gray-600 text-lg">Workout Insights</p>
          </div>
        `;

        openModal(content, { title: 'Success', size: 'md' });

      } else {
        alert("Error logging workout: " + (result.error || "Unknown error"));
      }
    } catch (err) {
      console.error("Log form error:", err);
      alert("Failed to log workout.");
    }
  });
});
