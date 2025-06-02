import { openModal, setupModalTriggers } from './modal.js';
import { renderSessionDetails } from './sessionRenderer.js';
import { renderTrendCharts } from './renderTrendCharts.js';
import { authFetch } from './auth/authFetch.js';

let lastViewedSessionIds = [];
let lastSessionDetails = [];

document.addEventListener('DOMContentLoaded', () => {
  setupModalTriggers();

  const calendarEl = document.getElementById('calendar');

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    height: 'auto',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: ''
    },
    events: async function (fetchInfo, successCallback, failureCallback) {
      try {
        const [sessionRes, goalsRes] = await Promise.all([
          authFetch('/api/sessions'),
          authFetch('/api/goals')
        ]);

        const [sessions, goals] = await Promise.all([
          sessionRes.json(),
          goalsRes.json()
        ]);

        // Group sessions by date
        const sessionsByDate = {};
        for (const session of sessions) {
          if (!sessionsByDate[session.date]) {
            sessionsByDate[session.date] = [];
          }
          sessionsByDate[session.date].push(session.id);
        }

        const sessionEvents = Object.entries(sessionsByDate).map(([date, sessionIds]) => ({
          title: sessionIds.length === 1 ? 'View Log' : 'View Logs',
          start: date,
          allDay: true,
          extendedProps: { sessionIds },
          color: '#3b82f6' // blue
        }));

        const goalEvents = goals
          .filter(goal => goal.deadline)
          .map(goal => ({
            title: `Goal: ${goal.name}`,
            start: goal.deadline.split('T')[0],
            allDay: true,
            color: '#f59e0b', // amber
            extendedProps: { goal },
            display: 'background' // or 'auto' if you want it to be a normal event
          }));

        successCallback([...sessionEvents, ...goalEvents]);
      } catch (err) {
        failureCallback(err);
      }
    },

    eventClick: async function (info) {
      const sessionIds = info.event.extendedProps.sessionIds;
      lastViewedSessionIds = sessionIds;

      try {
        lastSessionDetails = await Promise.all(
          sessionIds.map(id =>
            authFetch(`/api/session/${id}`).then(res => res.json())
          )
        );

        const content = `
          <div class="max-h-[80vh] overflow-y-auto pr-2 space-y-6">
            ${lastSessionDetails
              .map(data => `
                <div class="bg-white p-4 shadow rounded-lg border space-y-4">
                  ${renderGoalsSection(data.goals)}
                  ${renderSessionDetails(data)}
                </div>
              `)
              .join('')}
          </div>
        `;

        openModal(content, { title: 'Workout Sessions', size: 'xl' });
      } catch (err) {
        console.error('Failed to fetch session details:', err);
      }
    }
  });

  calendar.render();

  // Edit Journal Entry Handler
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-edit-journal]');
    if (btn) {
      const sessionId = btn.getAttribute('data-session-id');
      const rawText = decodeURIComponent(btn.getAttribute('data-raw-text'));

      const editModalHtml = `
        <div class="p-4">
          <h2 class="text-lg font-bold mb-2">Edit Journal Entry</h2>
          <textarea id="edit-raw-text" class="w-full h-48 p-2 border rounded">${rawText}</textarea>
          <div class="mt-4 flex justify-between">
            <button class="text-gray-600 underline" id="cancel-edit-journal">Cancel</button>
            <button 
              class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              data-save-journal
              data-session-id="${sessionId}"
            >
              Save Changes
            </button>
          </div>
        </div>
      `;

      openModal(editModalHtml, { title: 'Edit Journal Entry' });
    }
  });
});

// Save Journal Handler
document.addEventListener('click', async (e) => {
  const saveBtn = e.target.closest('button[data-save-journal]');
  if (saveBtn) {
    const sessionId = saveBtn.getAttribute('data-session-id');
    const newText = document.getElementById('edit-raw-text').value.trim();

    try {
      const res = await authFetch(`/api/edit-workout/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: newText })
      });

      const data = await res.json();

      if (!res.ok) {
        const errorMsg = data?.error || 'Failed to update workout.';
        throw new Error(errorMsg);
      }

      // Re-fetch updated session data
      lastSessionDetails = await Promise.all(
        lastViewedSessionIds.map(id =>
          authFetch(`/api/session/${id}`).then(res => res.json())
        )
      );

      const content = `
        <div class="max-h-[80vh] overflow-y-auto pr-2 space-y-6">
          ${lastSessionDetails
            .map(data => `
              <div class="bg-white p-4 shadow rounded-lg border space-y-4">
                ${renderGoalsSection(data.goals)}
                ${renderSessionDetails(data)}
              </div>
            `)
            .join('')}
        </div>
      `;

      openModal(content, { size: 'xl' });
    } catch (err) {
      console.error('Error saving journal entry:', err);
      alert('Failed to save journal entry. Can you ensure that input is a valid set of workout entries?');
    }
  }
});

// View Trends Handler
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('button[data-view-trends]');
  if (!btn) return;

  const sessionId = Number(btn.getAttribute('data-session-id'));

  try {
    const session = lastSessionDetails.find(s => s.id === sessionId);
    const sessionDate = session?.date?.split?.('T')?.[0] || new Date().toISOString().slice(0, 10);

    const res = await authFetch(`/api/workout-trends/${sessionId}?date=${sessionDate}&count=5`);
    const data = await res.json();

    const hasCharts = data && (
      (data.strength && Object.keys(data.strength).length > 0) ||
      (data.cardio && Object.keys(data.cardio).length > 0)
    );

    const modalContent = `
      <div class="p-4 space-y-6">
        <div class="relative flex items-center justify-center">
          <button class="absolute left-0 text-blue-600 hover:underline text-sm" id="back-to-sessions">
            ← Back to Sessions
          </button>
          <h2 class="text-2xl font-bold text-center">Session Insights</h2>
        </div>
        <p class="text-gray-600 text-lg text-center">Workout Summary</p>
        <div id="trend-tabs" class="mb-4 flex space-x-2 border-b"></div>
        <div id="trend-container" class="mt-4"></div>
        ${!hasCharts ? '<p class="text-center text-gray-500 mt-8">No workout logged.</p>' : ''}
      </div>
    `;

    openModal(modalContent, { title: 'Session Insights', size: 'xl' });

    if (hasCharts) {
      setTimeout(() => renderTrendCharts(data), 100);
    }
  } catch (err) {
    console.error('Failed to fetch trend data:', err);
    alert('Could not load trend insights.');
  }
});

// Back to Sessions from Trend Modal
document.addEventListener('click', (e) => {
  if (e.target.id === 'back-to-sessions') {
    const content = `
      <div class="max-h-[80vh] overflow-y-auto pr-2 space-y-6">
        ${lastSessionDetails
          .map(data => `
            <div class="bg-white p-4 shadow rounded-lg border space-y-4">
              ${renderGoalsSection(data.goals)}
              ${renderSessionDetails(data)}
            </div>
          `)
          .join('')}
      </div>
    `;
    openModal(content, { title: 'Workout Sessions', size: 'xl' });
  }
});

// Cancel Edit - Back to Sessions
document.addEventListener('click', (e) => {
  if (e.target.id === 'cancel-edit-journal') {
    const content = `
      <div class="max-h-[80vh] overflow-y-auto pr-2 space-y-6">
        ${lastSessionDetails
          .map(data => `
            <div class="bg-white p-4 shadow rounded-lg border space-y-4">
              ${renderGoalsSection(data.goals)}
              ${renderSessionDetails(data)}
            </div>
          `)
          .join('')}
      </div>
    `;
    openModal(content, { title: 'Workout Sessions', size: 'xl' });
  }
});

function renderGoalsSection(goals = []) {
  if (!goals.length) return '';

  return `
    <div class="border rounded-lg shadow-sm bg-gray-50">
      <div class="bg-blue-100 text-blue-800 px-4 py-2 rounded-t-lg">
        <h3 class="text-md font-semibold uppercase tracking-wide">Session Goals</h3>
      </div>
      <div class="px-4 py-3 space-y-3">
        ${goals.map(goal => `
          <div class="bg-white p-3 rounded-lg border border-gray-200 shadow-sm">
            <div class="flex justify-between items-start">
              <div>
                <p class="text-sm text-gray-500">Goal:</p>
                <p class="text-md font-semibold text-gray-800">${goal.name}</p>
              </div>
              ${goal.completed ? '<span class="text-green-600 text-sm font-medium">Completed</span>' : ''}
            </div>
            <div class="mt-2 text-sm text-gray-700">
              <p><strong>Exercise:</strong> ${goal.exercise_name} (${goal.exercise_type})</p>
              <p><strong>Type:</strong> ${goal.goal_type.replace('_', ' ')}</p>
              <ul class="list-disc list-inside mt-2">
                ${goal.targets.map(t => `
                  <li>${t.target_metric}: ${t.target_value}</li>
                `).join('')}
              </ul>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}
