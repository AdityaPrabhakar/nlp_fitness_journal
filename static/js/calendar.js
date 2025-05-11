// calendar.js
import { openModal } from './modal.js'; // Assuming modal logic is modular too

export function initCalendar(calendarEl, monthYearLabelEl, sessionModalEl, sessionDetailsEl) {
    const sessionsByDate = {};
    let currentDate = new Date();

    function formatDateKey(date) {
        return date.toISOString().split('T')[0];
    }

    function renderCalendar(date) {
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDay = firstDay.getDay();

        monthYearLabelEl.textContent = date.toLocaleDateString(undefined, {
            month: 'long',
            year: 'numeric'
        });

        calendarEl.innerHTML = '';

        for (let i = 0; i < startDay; i++) {
            calendarEl.appendChild(document.createElement('div'));
        }

        for (let i = 1; i <= lastDay.getDate(); i++) {
            const cellDate = new Date(year, month, i);
            const dateKey = formatDateKey(cellDate);
            const session = sessionsByDate[dateKey];

            const cell = document.createElement('div');
            cell.className = `p-3 border rounded text-center cursor-pointer transition-all duration-150 ${
                session ? 'bg-blue-100 hover:bg-blue-200' : 'bg-gray-50'
            }`;
            cell.innerText = i;

            if (session) {
                cell.onclick = () => {
                    fetch(`/api/session/${session.id}`)
                        .then(res => res.json())
                        .then(data => {
                            const entriesHtml = data.entries.map(entry => {
                                const entryLines = [];
                                if (entry.exercise) entryLines.push(`<p><strong>Exercise:</strong> ${entry.exercise}</p>`);
                                if (entry.type) entryLines.push(`<p><strong>Type:</strong> ${entry.type}</p>`);
                                if (entry.sets) entryLines.push(`<p><strong>Sets:</strong> ${entry.sets}</p>`);
                                if (entry.reps) entryLines.push(`<p><strong>Reps:</strong> ${entry.reps}</p>`);
                                if (entry.weight) entryLines.push(`<p><strong>Weight:</strong> ${entry.weight}</p>`);
                                if (entry.duration) entryLines.push(`<p><strong>Duration:</strong> ${entry.duration}</p>`);
                                if (entry.distance) entryLines.push(`<p><strong>Distance:</strong> ${entry.distance}</p>`);
                                if (entry.notes) entryLines.push(`<p><strong>Notes:</strong> ${entry.notes}</p>`);
                                return `<div class="mb-2 p-2 border rounded">${entryLines.join('')}</div>`;
                            }).join('');

                            openModal(`
                                <p><strong>Date:</strong> ${data.date}</p>
                                <p><strong>Session Notes:</strong> ${data.notes || 'None'}</p>
                                <p><strong>Raw Text:</strong> ${data.raw_text || 'None'}</p>
                                <hr class="my-2">
                                <h4 class="font-semibold mb-1">Entries</h4>
                                ${entriesHtml || '<p>No entries found.</p>'}
                            `);
                        });
                };
            }

            calendarEl.appendChild(cell);
        }
    }

    function changeMonth(offset) {
        currentDate.setMonth(currentDate.getMonth() + offset);
        renderCalendar(currentDate);
    }

    fetch('/api/sessions')
        .then(res => res.json())
        .then(data => {
            for (const session of data) {
                sessionsByDate[session.date] = session;
            }
            renderCalendar(currentDate);
        });

    return {
        renderCalendar,
        changeMonth
    };
}
