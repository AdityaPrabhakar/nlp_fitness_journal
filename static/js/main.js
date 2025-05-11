function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function destroyChart(chart) {
    if (chart) chart.destroy();
}

async function loadCardioChart() {
    const res = await fetch("/api/progress/cardio");
    const data = await res.json();
    const ctx = document.getElementById('cardioChart').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [
                {
                    label: 'Distance (mi)',
                    data: data.map(d => d.distance || 0),
                    borderColor: 'blue',
                    yAxisID: 'y1',
                    tension: 0.3
                },
                {
                    label: 'Duration (min)',
                    data: data.map(d => d.duration || 0),
                    borderColor: 'green',
                    yAxisID: 'y2',
                    tension: 0.3
                }
            ]
        },
        options: {
            scales: {
                y1: { type: 'linear', position: 'left' },
                y2: { type: 'linear', position: 'right', grid: { drawOnChartArea: false } }
            }
        }
    });
}

async function loadExerciseChart(type, exercise, canvasId) {
    const res = await fetch(`/api/progress/${type}/${exercise}`);
    const data = await res.json();
    const ctx = document.getElementById(canvasId).getContext('2d');

    if (window[canvasId + 'Chart']) {
        destroyChart(window[canvasId + 'Chart']);
    }

    const config = {
        type: type === 'cardio' ? 'line' : 'bar',
        data: {
            labels: data.map(d => d.date),
            datasets: type === 'cardio' ? [
                {
                    label: 'Distance (mi)',
                    data: data.map(d => d.distance || 0),
                    borderColor: 'purple',
                    yAxisID: 'y1',
                    tension: 0.3
                },
                {
                    label: 'Duration (min)',
                    data: data.map(d => d.duration || 0),
                    borderColor: 'orange',
                    yAxisID: 'y2',
                    tension: 0.3
                }
            ] : [
                {
                    label: 'Volume (sets × reps)',
                    data: data.map(d => d.volume || 0),
                    backgroundColor: 'red',
                    yAxisID: 'y1',
                    barThickness: 20
                },
                {
                    label: 'Max Weight (lbs)',
                    data: data.map(d => d.max_weight || 0),
                    backgroundColor: 'blue',
                    yAxisID: 'y2',
                    barThickness: 20
                }
            ]
        },
        options: {
            scales: {
                y1: { type: 'linear', position: 'left' },
                y2: { type: 'linear', position: 'right', grid: { drawOnChartArea: false } }
            }
        }
    };

    window[canvasId + 'Chart'] = new Chart(ctx, config);
}

async function loadLogTable(type, exercise, tableId) {
    const res = await fetch(`/api/logs/${type}/${exercise}`);
    const data = await res.json();

    const table = document.getElementById(tableId);
    const thead = table.querySelector("thead");
    const tbody = table.querySelector("tbody");

    if (type === 'cardio') {
        thead.innerHTML = "<tr><th>Date</th><th>Duration</th><th>Distance</th><th>Notes</th></tr>";
        tbody.innerHTML = data.map(entry =>
            `<tr>
                <td>${entry.date}</td>
                <td>${entry.duration ?? '-'}</td>
                <td>${entry.distance ?? '-'}</td>
                <td>${entry.notes ?? '-'}</td>
            </tr>`
        ).join("");
    } else {
        thead.innerHTML = "<tr><th>Date</th><th>Sets</th><th>Reps</th><th>Weight</th><th>Notes</th></tr>";
        tbody.innerHTML = data.map(entry =>
            `<tr>
                <td>${entry.date}</td>
                <td>${entry.sets ?? '-'}</td>
                <td>${entry.reps ?? '-'}</td>
                <td>${entry.weight ?? '-'}</td>
                <td>${entry.notes ?? '-'}</td>
            </tr>`
        ).join("");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById("cardioSelect")?.addEventListener('change', function (event) {
        const exercise = event.target.value;
        loadExerciseChart('cardio', exercise, 'cardioExerciseChart');
        loadLogTable('cardio', exercise, 'cardioLogTable');
    });

    document.getElementById("strengthSelect")?.addEventListener('change', function (event) {
        const exercise = event.target.value;
        loadExerciseChart('strength', exercise, 'strengthExerciseChart');
        loadLogTable('strength', exercise, 'strengthLogTable');
    });

    loadCardioChart();

    document.querySelectorAll('button[data-modal]').forEach(button => {
        button.addEventListener('click', function () {
            const modalId = this.getAttribute('data-modal');
            openModal(modalId);
        });
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const calendar = document.getElementById('calendar');
    const monthYearLabel = document.getElementById('monthYear');
    const modal = document.getElementById('session-modal');
    const sessionDetails = document.getElementById('session-details');
    const sessionsByDate = {};

    let currentDate = new Date();

    function formatDateKey(date) {
        return date.toISOString().split('T')[0];
    }

    function closeModal() {
        modal.classList.add('hidden');
    }
    window.closeModal = closeModal;

    function openModal(content) {
        sessionDetails.innerHTML = content;
        modal.classList.remove('hidden');
    }

    function renderCalendar(date) {
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDay = firstDay.getDay();

        monthYearLabel.textContent = date.toLocaleDateString(undefined, {
            month: 'long',
            year: 'numeric'
        });

        calendar.innerHTML = '';

        // Empty cells before first day
        for (let i = 0; i < startDay; i++) {
            calendar.appendChild(document.createElement('div'));
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

            calendar.appendChild(cell);
        }
    }

    fetch('/api/sessions')
        .then(res => res.json())
        .then(data => {
            for (const session of data) {
                sessionsByDate[session.date] = session;
            }
            renderCalendar(currentDate);
        });

    document.getElementById('prevMonth')?.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar(currentDate);
    });

    document.getElementById('nextMonth')?.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar(currentDate);
    });
});
