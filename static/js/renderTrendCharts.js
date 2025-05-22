export async function renderTrendCharts(data) {
  console.log('[renderTrendCharts] Starting chart render');

  const tabs = document.getElementById('trend-tabs');
  const container = document.getElementById('trend-container');
  tabs.innerHTML = '';
  container.innerHTML = '';

  const allItems = [
    ...data.strength.map((item, index) => ({ ...item, type: 'strength', id: `strength-${index}` })),
    ...data.cardio.map((item, index) => ({ ...item, type: 'cardio', id: `cardio-${index}` }))
  ];

  allItems.forEach((item, i) => {
    const label = item.exercise || item.activity;
    const tab = document.createElement('button');
    tab.className = `px-4 py-2 rounded-t text-sm font-medium ${
      i === 0 ? 'bg-white border-t border-l border-r' : 'bg-gray-100'
    }`;
    tab.textContent = label;
    tab.dataset.target = item.id;
    tab.onclick = () => {
      document.querySelectorAll('#trend-tabs button').forEach(btn =>
        btn.classList.remove('bg-white', 'border-t', 'border-l', 'border-r')
      );
      tab.classList.add('bg-white', 'border-t', 'border-l', 'border-r');
      document.querySelectorAll('.trend-panel').forEach(p => p.classList.add('hidden'));
      document.getElementById(item.id).classList.remove('hidden');
    };
    tabs.appendChild(tab);
  });

  allItems.forEach((item, index) => {
    const panel = document.createElement('div');
    panel.id = item.id;
    panel.className = `trend-panel ${index !== 0 ? 'hidden' : ''}`;

    // ========== CHART RENDERING FIRST ========== //
    const chartTypes = item.type === 'strength' ? ['Weight', 'Reps'] : ['Distance', 'Pace'];

    chartTypes.forEach(chartType => {
      const canvasId = `${item.id}-chart-${chartType.toLowerCase()}`;
      const history = item.type === 'strength'
        ? [
            ...item.history.flatMap(h =>
              h.sets.map(set => ({
                date: `${h.date} (Set ${set.set_number ?? '-'})`,
                reps: set.reps,
                weight: set.weight
              }))
            ),
            ...item.sets.map(set => ({
              date: `${data.session_date} (Set ${set.set_number ?? '-'})`,
              reps: set.reps,
              weight: set.weight
            }))
          ]
        : [
            ...item.history.map(h => ({ date: h.date, distance: h.distance, pace: h.pace })),
            { date: data.session_date, ...item.entry }
          ];

      history.sort((a, b) => new Date(a.date.split(' ')[0]) - new Date(b.date.split(' ')[0]));
      const labels = history.map(h => h.date);
      const dataPoints = history.map(h => h[chartType.toLowerCase()]);

      const hasValidData = dataPoints.some(val => val !== null && val !== undefined);

      if (!hasValidData) return; // 🚫 Skip chart rendering if all values are null/undefined

      const chartWrapper = document.createElement('div');
      chartWrapper.className = 'relative w-[90%] mx-auto h-72 mb-6';
      chartWrapper.innerHTML = `<canvas id="${canvasId}" class="absolute inset-0 w-full h-full"></canvas>`;
      panel.appendChild(chartWrapper); // ⬆️ Append chart BEFORE table

      const ctx = chartWrapper.querySelector('canvas').getContext('2d');

      new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: chartType,
            data: dataPoints,
            borderColor: chartType === 'Weight' || chartType === 'Distance' ? 'rgb(75,192,192)' : 'rgb(153,102,255)',
            backgroundColor: chartType === 'Weight' || chartType === 'Distance' ? 'rgba(75,192,192,0.2)' : 'rgba(153,102,255,0.2)',
            fill: true,
            tension: 0.3
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: chartType }
            }
          }
        }
      });
    });

    // ========== CURRENT SESSION NOTES ========== //
    if (item.notes) {
      const notesEl = document.createElement('p');
      notesEl.className = 'text-sm italic text-gray-600 mb-2';
      notesEl.textContent = `Notes: ${item.notes}`;
      panel.appendChild(notesEl);
    }

    // ========== CURRENT SESSION TABLE ========== //
    const currentTable = document.createElement('table');
    currentTable.className = 'w-full text-sm border border-gray-300 mb-4';
    if (item.type === 'strength') {
      currentTable.innerHTML = `
        <thead class="bg-gray-100"><tr><th>Set</th><th>Reps</th><th>Weight</th></tr></thead>
        <tbody>
          ${item.sets.map(s => `
            <tr class="text-center">
              <td>${s.set_number ?? '-'}</td>
              <td>${s.reps ?? '-'}</td>
              <td>${s.weight ?? '-'}</td>
            </tr>
          `).join('')}
        </tbody>`;
    } else {
      currentTable.innerHTML = `
        <thead class="bg-gray-100"><tr><th>Distance</th><th>Duration</th><th>Pace</th></tr></thead>
        <tbody>
          <tr class="text-center">
            <td>${item.entry.distance ?? '-'}</td>
            <td>${item.entry.duration ?? '-'}</td>
            <td>${item.entry.pace ?? '-'}</td>
          </tr>
        </tbody>`;
    }
    panel.appendChild(currentTable);

    const historyTitle = document.createElement('p');
    historyTitle.className = 'text-sm font-semibold text-gray-700 mb-2';
    historyTitle.textContent = 'Previous Sessions';
    panel.appendChild(historyTitle);

    [...item.history].sort((a, b) => new Date(b.date) - new Date(a.date)).forEach(h => {
      const div = document.createElement('div');
      div.className = 'mb-3';

      const meta = document.createElement('div');
      meta.className = 'text-xs italic text-gray-500 mb-1';
      meta.textContent = `${h.date}${h.notes ? ' – ' + h.notes : ''}`;
      div.appendChild(meta);

      const table = document.createElement('table');
      table.className = 'w-full text-xs border border-gray-200';
      if (item.type === 'strength') {
        table.innerHTML = `
          <thead class="bg-gray-50"><tr><th>Set</th><th>Reps</th><th>Weight</th></tr></thead>
          <tbody>
            ${h.sets.map((s, idx) => `
              <tr class="text-center">
                <td>${s.set_number ?? idx + 1}</td>
                <td>${s.reps ?? '-'}</td>
                <td>${s.weight ?? '-'}</td>
              </tr>
            `).join('')}
          </tbody>`;
      } else {
        table.innerHTML = `
          <thead class="bg-gray-50"><tr><th>Distance</th><th>Duration</th><th>Pace</th></tr></thead>
          <tbody>
            <tr class="text-center">
              <td>${h.distance ?? '-'}</td>
              <td>${h.duration ?? '-'}</td>
              <td>${h.pace ?? '-'}</td>
            </tr>
          </tbody>`;
      }

      div.appendChild(table);
      panel.appendChild(div);
    });

    container.appendChild(panel);
  });

  console.log('[renderTrendCharts] Chart rendering complete');
}
