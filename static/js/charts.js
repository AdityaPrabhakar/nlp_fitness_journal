export function destroyChart(chart) {
    if (chart) chart.destroy();
}

export async function loadCardioChart() {
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


export async function loadExerciseChart(type, exercise, canvasId) {
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