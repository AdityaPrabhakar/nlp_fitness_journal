import { openModal, setupModalTriggers } from './modal.js';
import { renderSessionDetails } from './sessionRenderer.js';
import { renderTrendCharts } from './renderTrendCharts.js';
import { authFetch} from "./auth/authFetch.js";

let lastViewedSessionIds = []; // Store sessionIds for re-rendering
let lastSessionDetails = [];   // Store full session data for "Back" use

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
        const res = await authFetch('/api/sessions');
        const sessions = await res.json();

        const sessionsByDate = {};
        for (const session of sessions) {
          if (!sessionsByDate[session.date]) {
            sessionsByDate[session.date] = [];
          }
          sessionsByDate[session.date].push(session.id);
        }

        const events = Object.entries(sessionsByDate).map(([date, sessionIds]) => ({
          title: sessionIds.length === 1 ? 'View Log' : 'View Logs',
          start: date,
          allDay: true,
          extendedProps: { sessionIds }
        }));

        successCallback(events);
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
                <div class="bg-white p-4 shadow rounded-lg border">
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
      const rawText = JSON.parse(btn.getAttribute('data-raw-text'));

      const editModalHtml = `
        <div class="p-4">
          <h2 class="text-lg font-bold mb-2">Edit Journal Entry</h2>
          <textarea id="edit-raw-text" class="w-full h-48 p-2 border rounded">${rawText}</textarea>
          <div class="mt-4 flex justify-between">
            <button 
              class="text-gray-600 underline"
              id="cancel-edit-journal"
            >
              Cancel
            </button>
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

      if (!res.ok) throw new Error('Failed to update workout');

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
              <div class="bg-white p-4 shadow rounded-lg border">
                ${renderSessionDetails(data)}
              </div>
            `)
            .join('')}
        </div>
      `;

      openModal(content, { size: 'xl' });
    } catch (err) {
      console.error('Error saving journal entry:', err);
      alert('Failed to update workout journal.');
    }
  }
});

// View Trends Handler
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('button[data-view-trends]');
  if (!btn) return;

  const sessionId = Number(btn.getAttribute('data-session-id'));
  console.log('sessionId:', sessionId)

  try {
    const session = lastSessionDetails.find(s => s.id === sessionId);
  console.log('session:', session);
  console.log('session.date:', session?.date);
  const sessionDate = session?.date?.split?.('T')?.[0] || new Date().toISOString().slice(0, 10);
    const res = await authFetch(`/api/workout-trends/${sessionId}?date=${sessionDate}&count=5`);
    const data = await res.json();

    const modalContent = `
    <div class="p-4 space-y-6">
      <div class="relative flex items-center justify-center">
        <button 
          class="absolute left-0 text-blue-600 hover:underline text-sm"
          id="back-to-sessions"
        >← Back to Sessions</button>
        <h2 class="text-2xl font-bold text-center">Session Insights</h2>
      </div>
      <p class="text-gray-600 text-lg text-center">Workout Summary</p>
      <div id="trend-tabs" class="mb-4 flex space-x-2 border-b"></div>
      <div id="trend-container" class="mt-4"></div>
    </div>
  `;


    openModal(modalContent, { title: 'Session Insights', size: 'xl' });

    setTimeout(() => renderTrendCharts(data), 100);
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
            <div class="bg-white p-4 shadow rounded-lg border">
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
            <div class="bg-white p-4 shadow rounded-lg border">
              ${renderSessionDetails(data)}
            </div>
          `)
          .join('')}
      </div>
    `;
    openModal(content, { title: 'Workout Sessions', size: 'xl' });
  }
});
