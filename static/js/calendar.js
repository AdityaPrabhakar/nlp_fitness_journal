import {closeModal, openModal, setupModalTriggers} from './modal.js';
import { renderSessionDetails } from './sessionRenderer.js';
import { renderTrendCharts } from './renderTrendCharts.js';
import { authFetch } from './auth/authFetch.js';
import {renderGoalCard} from "./goalCard.js";

let lastViewedSessionIds = [];
let lastSessionDetails = [];
let lastViewedGoals = [];

function showEditingWorkoutSummary() {
  console.log('[Modal] Showing loading workout summary modal...');
  const modalContent = `
    <div class="p-6 text-center space-y-4">
      <svg class="animate-spin h-6 w-6 mx-auto text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
      </svg>
      <p class="text-gray-700 text-sm">Editing entry and re-generating session data...</p>
    </div>
  `;
  openModal(modalContent, { title: 'Logging Workout...', size: 'xl' });
}

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
          authFetch('/api/goals/with-progress')
        ]);

        const [sessions, goals] = await Promise.all([
          sessionRes.json(),
          goalsRes.json()
        ]);

        // Group sessions by date
        const sessionsByDate = {};
        for (const session of sessions) {
          const dateStr = new Date(session.date).toISOString().split('T')[0]; // force ISO string
          if (!sessionsByDate[dateStr]) {
            sessionsByDate[dateStr] = [];
          }
          sessionsByDate[dateStr].push(session.id);
        }

        const sessionEvents = Object.entries(sessionsByDate).map(([date, sessionIds]) => ({
          title: sessionIds.length === 1 ? 'View Log' : 'View Logs',
          start: date,
          allDay: true,
          extendedProps: { sessionIds },
          color: '#3b82f6'
        }));

        // Group goals by end date
        const goalsByDate = {};
        for (const goal of goals) {
          if (!goal.end_date) continue;
          const date = goal.end_date.split('T')[0];
          if (!goalsByDate[date]) {
            goalsByDate[date] = [];
          }
          goalsByDate[date].push(goal);
        }

        const goalEvents = Object.entries(goalsByDate).map(([date, goalList]) => ({
          title: goalList.length > 1 ? 'Goals Due!' : 'Goal Due!',
          start: date,
          allDay: true,
          extendedProps: { goals: goalList },
          color: '#f59e0b',
          groupId: 'goal',
        }));


        successCallback([...sessionEvents, ...goalEvents]);
      } catch (err) {
        failureCallback(err);
      }
    },

    eventClick: async function (info) {
      const sessionIds = info.event.extendedProps.sessionIds;
      const clickedGoals = info.event.extendedProps.goals;


      // Handle workout session modal
      if (sessionIds) {
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

      else if (clickedGoals) {
        try {
          lastViewedGoals = clickedGoals;

          const container = document.createElement('div');
          container.className = 'max-h-[80vh] overflow-y-auto space-y-4 p-2';

          lastViewedGoals.forEach(goal => {
            const card = document.createElement('div');
            card.innerHTML = renderGoalCard(goal, { showDelete: false });
            container.appendChild(card);
          });

          openModal(container.outerHTML, { title: 'Goal Deadlines', size: 'xl' });
        } catch (err) {
          console.error('Failed to render goal cards:', err);
        }
      }
    }
  });

  calendar.render();

  // Delete Session Handler
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('button[data-delete-session]');
    if (!btn) return;

    const sessionId = btn.getAttribute('data-session-id');

    const confirmHtml = `
      <div class="bg-white rounded-xl shadow-lg p-6 max-w-md w-full">
        <h2 class="text-lg font-semibold mb-4">Confirm Delete</h2>
        <p class="mb-6 text-sm text-gray-600">Are you sure you want to delete this session? This action cannot be undone.</p>
        <div class="flex justify-end space-x-2">
          <button 
            id="cancel-delete-session" 
            class="px-4 py-2 text-sm rounded bg-gray-200 hover:bg-gray-300"
          >
            Cancel
          </button>
          <button 
            id="confirm-delete-session" 
            data-session-id="${sessionId}" 
            class="px-4 py-2 text-sm rounded bg-red-500 text-white hover:bg-red-600"
          >
            Delete
          </button>
        </div>
      </div>
    `;

    const overlay = document.createElement('div');
    overlay.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/40';
    overlay.setAttribute('data-modal-overlay', '');

    const modalWrapper = document.createElement('div');
    modalWrapper.className = 'z-60';
    modalWrapper.setAttribute('data-modal', '');
    modalWrapper.innerHTML = confirmHtml;

    overlay.appendChild(modalWrapper);
    document.body.appendChild(overlay);
  });


  // Confirm Delete Action
  document.addEventListener('click', async (e) => {
    if (e.target.id !== 'confirm-delete-session') return;

    const sessionId = e.target.getAttribute('data-session-id');

    try {
      const res = await authFetch(`/api/session/${sessionId}`, {
        method: 'DELETE'
      });

      if (!res.ok) throw new Error('Failed to delete session.');

      // Remove the modal and overlay
      const modalOverlay = document.querySelector('[data-modal-overlay]');
      if (modalOverlay) modalOverlay.remove();

      const modal = document.querySelector('[data-modal]');
      if (modal) modal.remove();

      closeModal();

      // Refresh the calendar or session list
      calendar.refetchEvents();

    } catch (err) {
      console.error('Error deleting session:', err);
      alert('Failed to delete session. Please try again.');
    }
  });


  // Cancel Delete Handler
  document.addEventListener('click', (e) => {
    if (e.target.id === 'cancel-delete-session') {
      const content = `
        <div class="max-h-[80vh] overflow-y-auto pr-2 space-y-6">
          ${lastSessionDetails
            .map(data => `
              <div class="bg-white p-4 shadow rounded-lg border space-y-4">
                ${renderSessionDetails(data)}
              </div>
            `)
            .join('')}
        </div>
      `;
      // Remove the modal and overlay
      const modalOverlay = document.querySelector('[data-modal-overlay]');
      if (modalOverlay) modalOverlay.remove();

      const modal = document.querySelector('[data-modal]');

      openModal(content, { title: 'Workout Sessions', size: 'xl' });
    }
  });

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

    showEditingWorkoutSummary();

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
                ${renderSessionDetails(data)}
              </div>
            `)
            .join('')}
        </div>
      `;

      openModal(content, { size: 'xl' });
    } catch (err) {
      console.error('Error saving journal entry:', err);
      alert('Failed to save journal entry. Please check your input format.');
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
    const rawDate = session?.date;
    const sessionDate = rawDate
      ? new Date(rawDate).toISOString().slice(0, 10)
      : new Date().toISOString().slice(0, 10);

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

// Back and Cancel Handlers
document.addEventListener('click', (e) => {
  if (e.target.id === 'back-to-sessions' || e.target.id === 'cancel-edit-journal') {
    const content = `
      <div class="max-h-[80vh] overflow-y-auto pr-2 space-y-6">
        ${lastSessionDetails
          .map(data => `
            <div class="bg-white p-4 shadow rounded-lg border space-y-4">
              ${renderSessionDetails(data)}
            </div>
          `)
          .join('')}
      </div>
    `;
    openModal(content, { title: 'Workout Sessions', size: 'xl' });
  }
});



