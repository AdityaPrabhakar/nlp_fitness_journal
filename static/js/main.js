import { destroyChart, loadCardioChart, loadExerciseChart } from './charts.js';
import { loadLogTable } from './log.js';
import { initCalendar } from './calendar.js';
import { setupModalTriggers, closeModal } from './modal.js';

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

    // Calendar Initialization
    const calendar = document.getElementById('calendar');
    const monthYearLabel = document.getElementById('monthYear');
    const sessionModal = document.getElementById('session-modal');
    const sessionDetails = document.getElementById('session-details');

    const { changeMonth } = initCalendar(calendar, monthYearLabel, sessionModal, sessionDetails);

    document.getElementById('prevMonth')?.addEventListener('click', () => {
        changeMonth(-1);
    });

    document.getElementById('nextMonth')?.addEventListener('click', () => {
        changeMonth(1);
    });

    // Modal global access
    window.closeModal = closeModal;
});
