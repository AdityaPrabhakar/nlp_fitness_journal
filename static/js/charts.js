// Helper function to destroy the existing chart
export function destroyChart(chart) {
    if (chart) chart.destroy();
}

// Function to load the cardio chart (distance and duration)
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

// Function to load exercise-specific charts (strength or cardio)
export async function loadExerciseChart(type, exercise, canvasId) {
    const res = await fetch(`/api/progress/${type}/${exercise}`);
    const data = await res.json();
    const ctx = document.getElementById(canvasId).getContext('2d');

    if (window[canvasId + 'Chart']) {
        destroyChart(window[canvasId + 'Chart']);
    }

    // Prepare the dataset with reps, weight, and set_number
    const weightData = data.map(d => ({
        set_number: d.set_number,
        weight: d.weight,
        date: d.date
    }));

    const repsData = data.map(d => ({
        set_number: d.set_number,
        reps: d.reps,
        date: d.date
    }));

    let datasets = [];

    if (type === 'cardio') {
        // Cardio charts (Line chart)
        datasets = [
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
        ];
    } else {
        // Strength charts (Bar chart)
        datasets = [
            {
                label: 'Weight (lbs)',
                data: weightData.map(d => d.weight),
                backgroundColor: 'blue',  // Color for weight bars
                yAxisID: 'y1',
                barThickness: 20
            },
            {
                label: 'Reps',
                data: repsData.map(d => d.reps),
                backgroundColor: 'green',  // Color for reps bars
                yAxisID: 'y2',
                barThickness: 20
            }
        ];
    }

    const config = {
        type: type === 'cardio' ? 'line' : 'bar',  // Cardio gets a line chart, strength gets a bar chart
        data: {
            labels: data.map(d => d.date),  // Use the date as labels on the x-axis
            datasets: datasets
        },
        options: {
            scales: {
                y1: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Weight (lbs)' }
                },
                y2: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Reps' },
                    grid: { drawOnChartArea: false }
                },
                x: {
                    type: 'category',
                    title: { display: true, text: 'Date' },
                    labels: data.map(d => d.date)  // Labels will be the workout dates
                },
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        // Customize the tooltip to show both reps and weight for each set
                        label: function(tooltipItem) {
                            const dataSet = tooltipItem.datasetIndex === 0 ? weightData : repsData;
                            const setData = dataSet[tooltipItem.dataIndex];  // Get the set data based on index

                            if (tooltipItem.datasetIndex === 0) {
                                // Weight dataset
                                return `Set ${setData.set_number}: ${setData.weight} lbs`;
                            } else if (tooltipItem.datasetIndex === 1) {
                                // Reps dataset
                                return `Set ${setData.set_number}: ${setData.reps} reps`;
                            }
                        }
                    }
                }
            }
        }
    };

    window[canvasId + 'Chart'] = new Chart(ctx, config);
}
