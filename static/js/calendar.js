import { openModal } from './modal.js';
import { showPRToast } from './toast.js';

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
                cell.onclick = () => loadAndRenderModal(sessions);
            }

            calendarEl.appendChild(cell);
        }
    }

    function loadAndRenderModal(sessions) {
        Promise.all(sessions.map(session =>
            fetch(`/api/session/${session.id}`).then(res => res.json())
                .then(data => ({ ...data, session_id: session.id }))
        )).then(allData => {
            renderModal(allData);
        });
    }

    function renderModal(allData) {
        const content = allData.map((data, index) => {
            const rawTextId = `raw-text-${data.session_id}`;
            const editBtnId = `edit-btn-${data.session_id}`;
            const saveBtnId = `save-btn-${data.session_id}`;

            const entriesHtml = data.entries.map(entry => {
                const lines = [];
                if (entry.exercise) lines.push(`<p><strong>Exercise:</strong> ${entry.exercise}</p>`);
                if (entry.type) lines.push(`<p><strong>Type:</strong> ${entry.type}</p>`);

                if (entry.type === "strength" && entry.sets_details?.length) {
                    const sets = entry.sets_details.map(set =>
                        `<li>Set ${set.set_number}: ${set.reps ?? "X"} reps @ ${set.weight ?? "X"} lbs</li>`
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
                <div class="mb-6 border border-gray-300 rounded p-3">
                    <p class="font-semibold">Session ${index + 1}</p>
                    <p><strong>Notes:</strong> ${data.notes || 'None'}</p>
                    <label class="block mt-2 text-sm font-medium text-gray-700">Raw Text:</label>
                    <textarea id="${rawTextId}" class="w-full border rounded p-2 mt-1 text-sm" rows="4" disabled>${data.raw_text || ''}</textarea>
                    <div class="mt-2 space-x-2">
                        <button id="${editBtnId}" class="px-3 py-1 text-blue-600 border border-blue-600 rounded text-sm hover:bg-blue-50">Edit Journal Entry</button>
                        <button id="${saveBtnId}" class="px-3 py-1 text-white bg-blue-600 hover:bg-blue-700 rounded text-sm hidden">Save Changes</button>
                    </div>
                    <hr class="my-3" />
                    <div>${entriesHtml || '<p>No entries</p>'}</div>
                </div>
            `;
        }).join('');

        openModal(`<p><strong>Date:</strong> ${allData[0]?.date}</p><div class="mt-4">${content}</div>`);

        allData.forEach(data => {
            const sessionId = data.session_id;
            const textarea = document.getElementById(`raw-text-${sessionId}`);
            const editBtn = document.getElementById(`edit-btn-${sessionId}`);
            const saveBtn = document.getElementById(`save-btn-${sessionId}`);

            if (editBtn && textarea && saveBtn) {
                editBtn.addEventListener('click', () => {
                    textarea.disabled = false;
                    textarea.focus();
                    saveBtn.classList.remove('hidden');
                    editBtn.remove(); // Remove edit button after making textarea editable
                });

                saveBtn.addEventListener('click', () => {
                    const updatedRaw = textarea.value;

                    fetch(`/api/edit-workout/${sessionId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ raw_text: updatedRaw })
                    }).then(async response => {
                        if (response.ok) {
                            const result = await response.json();

                            fetch(`/api/session/${sessionId}`)
                                .then(res => res.json())
                                .then(updatedSession => {
                                    renderModal([{ ...updatedSession, session_id: sessionId }]);
                                    refreshCalendar();

                                    if (result.new_prs && result.new_prs.length > 0) {
                                        showPRToast(result.new_prs);
                                    }
                                });
                        } else {
                            alert('Failed to update workout.');
                        }
                    });
                });
            }
        });
    }

    function changeMonth(offset) {
        currentDate.setMonth(currentDate.getMonth() + offset);
        renderCalendar(currentDate);
    }

    function refreshCalendar() {
        fetch('/api/sessions')
            .then(res => res.json())
            .then(data => {
                Object.keys(sessionsByDate).forEach(key => delete sessionsByDate[key]);
                for (const session of data) {
                    const dateKey = session.date;
                    if (!sessionsByDate[dateKey]) {
                        sessionsByDate[dateKey] = [];
                    }
                    sessionsByDate[dateKey].push(session);
                }
                renderCalendar(currentDate);
            });
    }

    refreshCalendar();

    return {
        renderCalendar,
        changeMonth,
        refreshCalendar
    };
}
