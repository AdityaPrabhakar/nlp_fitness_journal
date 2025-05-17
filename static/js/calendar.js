// static/js/calendar.js
import { openModal, setupModalTriggers } from './modal.js';
import { renderSessionDetails } from './sessionRenderer.js';


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
        const res = await fetch('/api/sessions');
        const sessions = await res.json();

        // Group sessions by date
        const sessionsByDate = {};
        for (const session of sessions) {
          if (!sessionsByDate[session.date]) {
            sessionsByDate[session.date] = [];
          }
          sessionsByDate[session.date].push(session.id);
        }

        // Create one event per date
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

      try {
        const sessionDetails = await Promise.all(
          sessionIds.map(id =>
            fetch(`/api/session/${id}`).then(res => res.json())
          )
        );

        const content = `
          <div class="max-h-[80vh] overflow-y-auto pr-2 space-y-6">
            ${sessionDetails
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
});