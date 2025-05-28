export function renderSessionDetails(data) {
  const entriesHtml = data.entries.map(entry => {
    let html = `<div class="mb-4 border-b pb-4">`;
    if (entry.exercise) html += `<p><strong>Exercise:</strong> ${entry.exercise}</p>`;
    if (entry.type) html += `<p><strong>Type:</strong> ${entry.type}</p>`;

    if (entry.type === "strength" && entry.sets_details?.length) {
      html += `<ul class="list-disc list-inside pl-4">`;
      for (const set of entry.sets_details) {
        html += `<li>Set ${set.set_number}: ${set.reps ?? "X"} reps @ ${set.weight ?? "X"} lbs</li>`;
      }
      html += `</ul>`;
    }

    if (entry.type === "cardio") {
      if (entry.duration) html += `<p><strong>Duration:</strong> ${entry.duration} min</p>`;
      if (entry.distance) html += `<p><strong>Distance:</strong> ${entry.distance} miles</p>`;
    }

    if (entry.notes) html += `<p><strong>Notes:</strong> ${entry.notes}</p>`;
    html += `</div>`;
    return html;
  }).join('');

  return `
    <p class="mb-2"><strong>Date:</strong> ${data.date}</p>
    <p class="mb-2 text-sm text-gray-500"><strong>Session ID:</strong> ${data.id}</p>
    ${data.notes ? `<p class="mb-2"><strong>Session Notes:</strong> ${data.notes}</p>` : ''}
    <div class="mb-4 p-3 bg-gray-100 rounded-md relative">
      <p class="font-semibold mb-1">Journal Entry:</p>
      <pre class="whitespace-pre-wrap text-sm text-gray-800">${data.raw_text}</pre>
      <button 
        class="absolute top-2 right-2 text-sm text-blue-600 hover:underline"
        data-edit-journal
        data-session-id="${data.id}" 
        data-raw-text="${encodeURIComponent(data.raw_text)}"
      >
        Edit
      </button>
    </div>
    <div class="mt-4">${entriesHtml || '<p>No entries found.</p>'}</div>
    <div class="mt-6 text-right">
      <button
        class="inline-block text-blue-700 hover:underline text-sm font-medium"
        data-view-trends
        data-session-id="${data.id}"
      >
        View Session Insights
      </button>
    </div>
  `;
}
