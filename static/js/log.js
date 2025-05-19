import { showPRToast } from './toast.js';
import { openModal, setupModalTriggers } from './modal.js';

document.addEventListener('DOMContentLoaded', () => {
  setupModalTriggers();
  const logForm = document.getElementById('logForm');
  if (!logForm) return;

  logForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const entryText = document.getElementById('entryText').value.trim();
    if (!entryText) return;

    try {
      const response = await fetch('/api/log-workout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entry: entryText })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        document.getElementById('entryText').value = '';

        if (result.new_prs?.length) {
          showPRToast(result.new_prs);
        }

        const trendRes = await fetch(`/api/workout-trends/${result.session_id}`);
        const trendData = await trendRes.json();

        let modalContent = `
          <div class="p-4 space-y-6">
            <h2 class="text-2xl font-bold text-center">Journal Entry Created! 🥳</h2>
            <p class="text-gray-600 text-lg text-center">Workout Summary</p>
            <div id="trend-tabs" class="mb-4 flex space-x-2 border-b"></div>
            <div id="trend-container" class="mt-4"></div>
          </div>
        `;

        openModal(modalContent, { title: 'Workout Summary', size: 'xl' });

        setTimeout(() => renderTrendCharts(trendData), 100);
      } else {
        alert("Error logging workout: " + (result.error || "Unknown error"));
      }
    } catch (err) {
      console.error("Log form error:", err);
      alert("Failed to log workout.");
    }
  });
});

function renderTrendCharts(data) {
  const tabs = document.getElementById('trend-tabs');
  const container = document.getElementById('trend-container');
  tabs.innerHTML = '';
  container.innerHTML = '';

  const allItems = [
    ...data.strength.map((item, index) => ({ ...item, type: 'strength', id: `strength-${index}` })),
    ...data.cardio.map((item, index) => ({ ...item, type: 'cardio', id: `cardio-${index}` }))
  ];

  allItems.forEach((item, i) => {
    const tab = document.createElement('button');
    tab.className = `px-4 py-2 rounded-t text-sm font-medium ${
      i === 0 ? 'bg-white border-t border-l border-r' : 'bg-gray-100'
    }`;
    tab.textContent = item.exercise || item.activity;
    tab.dataset.target = item.id;
    tab.onclick = () => {
      document.querySelectorAll('#trend-tabs button').forEach(btn => btn.classList.remove('bg-white', 'border-t', 'border-l', 'border-r'));
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

    const canvasId = `${item.id}-chart`;
    const chartWrapper = document.createElement('div');
    chartWrapper.className = 'relative w-[90%] mx-auto h-72 mb-6';
    chartWrapper.innerHTML = `<canvas id="${canvasId}" class="absolute inset-0 w-full h-full"></canvas>`;
    panel.appendChild(chartWrapper);

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
          <thead class="bg-gray-50"><tr><th>Reps</th><th>Weight</th></tr></thead>
          <tbody>
            ${h.sets.map(s => `
              <tr class="text-center">
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

    const ctx = document.getElementById(canvasId).getContext('2d');

    const history = item.type === 'strength'
      ? [
          ...item.history.flatMap(h => h.sets.map(set => ({ date: h.date, reps: set.reps, weight: set.weight }))),
          ...item.sets.map(set => ({ date: new Date().toISOString().split('T')[0], reps: set.reps, weight: set.weight }))
        ]
      : [
          ...item.history.map(h => ({ date: h.date, distance: h.distance, pace: h.pace })),
          { date: new Date().toISOString().split('T')[0], ...item.entry }
        ];

    history.sort((a, b) => new Date(a.date) - new Date(b.date));
    const labels = history.map(h => h.date);

    const datasets = item.type === 'strength'
      ? [
          {
            label: 'Weight',
            data: history.map(h => h.weight),
            borderColor: 'rgb(75,192,192)',
            backgroundColor: 'rgba(75,192,192,0.2)',
            yAxisID: 'y'
          },
          {
            label: 'Reps',
            data: history.map(h => h.reps),
            borderColor: 'rgb(153,102,255)',
            backgroundColor: 'rgba(153,102,255,0.2)',
            yAxisID: 'y1'
          }
        ]
      : [
          {
            label: 'Distance',
            data: history.map(h => h.distance),
            borderColor: 'rgb(255, 159, 64)',
            backgroundColor: 'rgba(255,159,64,0.2)',
            yAxisID: 'y'
          },
          {
            label: 'Pace',
            data: history.map(h => h.pace),
            borderColor: 'rgb(54, 162, 235)',
            backgroundColor: 'rgba(54,162,235,0.2)',
            yAxisID: 'y1'
          }
        ];

    new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
          y: { beginAtZero: true, position: 'left', title: { display: true, text: datasets[0].label } },
          y1: { beginAtZero: true, position: 'right', title: { display: true, text: datasets[1].label }, grid: { drawOnChartArea: false } }
        }
      }
    });
  });
}
