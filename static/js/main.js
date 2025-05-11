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
    const modal = document.getElementById('session-modal');
    const sessionDetails = document.getElementById('session-details');

    if (!calendar) return; // only run on pages that have a calendar

    const sessionsByDate = {};

    function formatDateKey(date) {
        return date.toISOString().split('T')[0];
    }

    function closeModal() {
        modal.classList.add('hidden');
    }

    window.closeModal = closeModal; // Make it available to the inline button

    function openModal(content) {
        sessionDetails.innerHTML = content;
        modal.classList.remove('hidden');
    }

    function renderCalendar() {
        const today = new Date();
        const start = new Date(today.getFullYear(), today.getMonth(), 1);
        const end = new Date(today.getFullYear(), today.getMonth() + 1, 0);

        calendar.innerHTML = '';

        for (let i = 1; i <= end.getDate(); i++) {
            const date = new Date(today.getFullYear(), today.getMonth(), i);
            const dateKey = formatDateKey(date);

            const hasSession = sessionsByDate[dateKey];
            const cell = document.createElement('div');
            cell.className = `p-3 border rounded text-center cursor-pointer ${hasSession ? 'bg-blue-100 hover:bg-blue-200' : 'bg-gray-50'}`;
            cell.innerText = i;

            if (hasSession) {
                cell.onclick = () => {
                    const session = sessionsByDate[dateKey];
                    fetch(`/api/session/${session.id}`)
                        .then(res => res.json())
                        .then(data => {
                            const entriesHtml = data.entries.map(entry => `
                                <div class="mb-2 p-2 border rounded">
                                    <p><strong>Exercise:</strong> ${entry.exercise}</p>
                                    <p><strong>Type:</strong> ${entry.type}</p>
                                    <p><strong>Sets:</strong> ${entry.sets}</p>
                                    <p><strong>Reps:</strong> ${entry.reps}</p>
                                    <p><strong>Weight:</strong> ${entry.weight}</p>
                                    <p><strong>Duration:</strong> ${entry.duration}</p>
                                    <p><strong>Distance:</strong> ${entry.distance}</p>
                                    <p><strong>Notes:</strong> ${entry.notes || 'None'}</p>
                                </div>
                            `).join('');

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
            renderCalendar();
        });
});

