// static/js/logWorkout.js
export function setupWorkoutLogging(calendarManager) {
    const logForm = document.getElementById('logForm');
    if (!logForm) return;

    logForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const entryText = document.getElementById('entryText').value.trim();
        if (!entryText) return;

        const response = await fetch('/api/log-workout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ entry: entryText })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            window.location.reload(); // Let server flash message show
        } else {
            alert("Error logging workout: " + (result.message || result.error));
        }
    });
}
