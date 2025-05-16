import { showPRToast } from './toast.js';

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
            alert(result.message); // ✅ Display flash-like success
            document.getElementById('entryText').value = '';
            calendarManager.refreshCalendar(); // ✅ Refresh calendar

            if (result.new_prs && result.new_prs.length > 0) {
                showPRToast(result.new_prs); // 🎉 Show PR toast if any
            }
        } else {
            alert("Error logging workout: " + (result.message || result.error));
        }
    });
}
