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
