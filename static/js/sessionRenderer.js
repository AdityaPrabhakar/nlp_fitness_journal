export function renderSessionDetails(data) {
  function renderGoalsSection(goals = []) {
    if (!goals.length) return '';

    return `
      <div class="mt-2 mb-4">
        <p class="font-semibold mb-2">Related Goals:</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          ${goals.map(goal => {
            const bgColor = goal.is_complete
              ? 'bg-green-100 border-green-300'
              : goal.is_expired
                ? 'bg-red-100 border-red-300'
                : 'bg-white border-gray-200';

            return `
              <div class="${bgColor} p-3 rounded-lg border shadow-sm">
                <p class="font-semibold text-sm">${goal.name}</p>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

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
      ${renderGoalsSection(data.goals)}
      ${data.notes ? `<p class="mb-2"><strong>Session Notes:</strong> ${data.notes}</p>` : ''}
      
      <p class="font-semibold mb-1">Journal Entry:</p>
      <div class="mb-4 p-3 bg-gray-100 rounded-md relative">
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
