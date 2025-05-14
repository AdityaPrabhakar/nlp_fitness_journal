import { openModal } from './modal.js';

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
            const sessions = sessionsByDate[dateKey] || [];

            const cell = document.createElement('div');
            cell.className = `p-3 border rounded text-center transition-all duration-150 cursor-pointer ${
                sessions.length ? 'bg-blue-100 hover:bg-blue-200' : 'bg-gray-50'
            }`;
            cell.innerHTML = `<div>${i}</div>` +
                (sessions.length > 1 ? `<div class="text-xs text-blue-700 mt-1">${sessions.length} sessions</div>` : '');

            if (sessions.length) {
                cell.onclick = () => {
                    Promise.all(sessions.map(session =>
                        fetch(`/api/session/${session.id}`).then(res => res.json())
                    )).then(allData => {
                        const content = allData.map((data, index) => {
                            const entriesHtml = data.entries.map(entry => {
                                const lines = [];
                                if (entry.exercise) lines.push(`<p><strong>Exercise:</strong> ${entry.exercise}</p>`);
                                if (entry.type) lines.push(`<p><strong>Type:</strong> ${entry.type}</p>`);

                                if (entry.type === "strength" && entry.sets_details?.length) {
                                    const sets = entry.sets_details.map(set =>
                                        `<li>Set ${set.set_number}: ${set.reps} reps @ ${set.weight !== null && set.weight !== undefined ? set.weight : "X"} lbs</li>`
                                    ).join('');
                                    lines.push(`<p><strong>Sets:</strong></p><ul class="list-disc list-inside">${sets}</ul>`);
                                }

                                if (entry.type === "cardio") {
                                    if (entry.duration) lines.push(`<p><strong>Duration:</strong> ${entry.duration} min</p>`);
                                    if (entry.distance) lines.push(`<p><strong>Distance:</strong> ${entry.distance} miles</p>`);
                                    if (entry.cardio_notes) lines.push(`<p><strong>Cardio Notes:</strong> ${entry.cardio_notes}</p>`);
                                }

                                if (entry.notes) lines.push(`<p><strong>Notes:</strong> ${entry.notes}</p>`);

                                return `<div class="mb-2 p-2 border rounded">${lines.join('')}</div>`;
                            }).join('');


                            return `
                                <div class="mb-4">
                                    <p class="font-semibold">Session ${index + 1}</p>
                                    <p><strong>Notes:</strong> ${data.notes || 'None'}</p>
                                    <p><strong>Raw:</strong> ${data.raw_text || 'None'}</p>
                                    <hr class="my-2" />
                                    <div>${entriesHtml || '<p>No entries</p>'}</div>
                                </div>
                            `;
                        }).join('');

                        openModal(`<p><strong>Date:</strong> ${allData[0]?.date}</p><div class="mt-2">${content}</div>`);
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
                const dateKey = session.date;
                if (!sessionsByDate[dateKey]) {
                    sessionsByDate[dateKey] = [];
                }
                sessionsByDate[dateKey].push(session);
            }
            renderCalendar(currentDate);
        });

    return {
        renderCalendar,
        changeMonth
    };
}
