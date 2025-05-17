import { destroyChart, loadCardioChart, loadExerciseChart } from './charts.js';
import { loadLogTable } from './log.js';
import { initCalendar } from './calendar.js';
import { setupModalTriggers, closeModal } from './modal.js';
import { setupWorkoutLogging } from './logWorkout.js';

document.addEventListener('DOMContentLoaded', () => {

    // Chart + Table Listeners
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
    setupModalTriggers();

    // Calendar Setup
    const calendar = document.getElementById('calendar');
    const monthYearLabel = document.getElementById('monthYear');
    const sessionModal = document.getElementById('session-modal');
    const sessionDetails = document.getElementById('session-details');

    const calendarManager = initCalendar(calendar, monthYearLabel, sessionModal, sessionDetails);

    document.getElementById('prevMonth')?.addEventListener('click', () => {
        calendarManager.changeMonth(-1);
    });

    document.getElementById('nextMonth')?.addEventListener('click', () => {
        calendarManager.changeMonth(1);
    });

    // Toggle calendar visibility
    const toggleBtn = document.getElementById('toggleCalendarBtn');
    const calendarContainer = document.getElementById('calendarContainer');

    toggleBtn?.addEventListener('click', () => {
        const isHidden = calendarContainer.classList.toggle('hidden');
        toggleBtn.textContent = isHidden ? "View Workout Journal Entries" : "Hide Workout Journal Entries";
    });

    // ✅ Workout logging (moved out)
    setupWorkoutLogging(calendarManager);

    // Modal global access
    window.closeModal = closeModal;
});
