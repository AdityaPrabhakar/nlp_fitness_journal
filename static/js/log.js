export async function loadLogTable(type, exercise, tableId) {
    const res = await fetch(`/api/logs/${type}/${exercise}`);
    const data = await res.json();

    const table = document.getElementById(tableId);
    const thead = table.querySelector("thead");
    const tbody = table.querySelector("tbody");

    if (type === 'cardio') {
        thead.innerHTML = "<tr><th>Date</th><th>Duration</th><th>Distance</th></tr>";

        const rows = data.map(entry => {
            const mainRow = `
                <tr>
                    <td>${entry.date}</td>
                    <td>${entry.duration ?? '-'}</td>
                    <td>${entry.distance ?? '-'}</td>
                </tr>
            `;

            const noteRow = entry.notes
                ? `<tr><td colspan="3"><em>Note:</em> ${entry.notes}</td></tr>`
                : '';

            return mainRow + noteRow;
        }).join('');

        tbody.innerHTML = rows;
    } else {
        thead.innerHTML = "<tr><th>Date</th><th>Set</th><th>Reps</th><th>Weight</th></tr>";

        // Group sets by date
        const grouped = {};
        data.forEach(entry => {
            if (!grouped[entry.date]) {
                grouped[entry.date] = [];
            }
            grouped[entry.date].push(entry);
        });

        // Build rows: one per set, plus a notes row per workout
        const rows = Object.entries(grouped).map(([date, sets]) => {
            const setRows = sets.map((set, i) => `
                <tr>
                    <td>${i === 0 ? date : ''}</td>
                    <td>${set.sets ?? 'X'}</td>
                    <td>${set.reps ?? 'X'}</td>
                    <td>${set.weight != null ? set.weight : 'X'}</td>
                </tr>
            `).join('');

            const noteRow = sets[0].notes
                ? `<tr><td colspan="4"><em>Note:</em> ${sets[0].notes}</td></tr>`
                : '';

            return setRows + noteRow;
        }).join('');

        tbody.innerHTML = rows;
    }
}
