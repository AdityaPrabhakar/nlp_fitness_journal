import {authFetch} from "../auth/authFetch.js";

const sessionTableContainer = document.getElementById("sessionTableContainer");


export async function renderSessionTable(exercise, startDate, endDate) {
  const params = new URLSearchParams({ exercise });
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  try {
    const res = await authFetch(`/api/sessions/by-exercise?${params}`);
    const sessions = await res.json();

    if (!Array.isArray(sessions)) {
      sessionTableContainer.innerHTML = `<p class="text-red-600">Failed to load session table.</p>`;
      return;
    }

    let tableHtml = `
      <table class="min-w-full divide-y divide-gray-200 mt-4 text-sm text-left">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-2">Date</th>
            <th class="px-4 py-2">Exercise</th>
            <th class="px-4 py-2">Type</th>
            <th class="px-4 py-2">Details</th>
            <th class="px-4 py-2">Notes</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-100">
    `;

    for (const session of sessions) {
      const date = new Date(session.date).toLocaleDateString();

      for (const entry of session.entries) {
        let details = "";

        if (entry.type === "strength") {
          if (Array.isArray(entry.sets)) {
            details = entry.sets
              .map(set => `Set ${set.set_number}: ${set.reps ?? "-"} reps @ ${set.weight ?? "-"} lbs`)
              .join("<br>");
          } else {
            details = "No set data";
          }
        } else if (entry.type === "cardio") {
          details = `${entry.distance ?? "-"} mi in ${entry.duration ?? "-"} min`;
        }

        tableHtml += `
          <tr>
            <td class="px-4 py-2">${date}</td>
            <td class="px-4 py-2">${entry.exercise}</td>
            <td class="px-4 py-2 capitalize">${entry.type}</td>
            <td class="px-4 py-2">${details}</td>
            <td class="px-4 py-2">${entry.notes || "-"}</td>
          </tr>
        `;
      }
    }

    tableHtml += `</tbody></table>`;
    sessionTableContainer.innerHTML = tableHtml;
  } catch (err) {
    console.error("[renderSessionTable] Failed:", err);
    sessionTableContainer.innerHTML = `<p class="text-red-600">Error loading sessions.</p>`;
  }
}