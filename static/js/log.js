export async function loadLogTable(type, exercise, tableId) {
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