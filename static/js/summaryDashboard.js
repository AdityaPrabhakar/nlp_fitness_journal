async function fetchJSON(url) {
  const res = await fetch(url);
  const data = await res.json();
  if (!data.success) throw new Error('API error');
  return data;
}

async function renderSummaryStats() {
  console.log("[INFO] Fetching summary stats...");
  const data = await fetchJSON('/api/summary/overview?days=7');
  const row = document.getElementById('summary-row');

  const items = [
    { label: "Total Sessions", count: data.total_sessions },
    { label: "Strength Workouts", count: data.strength_sessions },
    { label: "Cardio Workouts", count: data.cardio_sessions },
  ];

  row.innerHTML = items.map(i => `
    <div class="bg-white shadow rounded p-4 text-center">
      <div class="text-2xl font-bold">${i.count}</div>
      <div class="text-sm text-gray-500">${i.label}</div>
    </div>
  `).join('');
}

async function renderCardioDurationChart() {
  console.log("[INFO] Fetching cardio duration...");
  const data = await fetchJSON('/api/summary/cardio?days=7');
  const ctx = document.getElementById('cardioDurationChart').getContext('2d');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.daily_cardio.map(d => d.date),
      datasets: [{
        label: 'Duration (min)',
        data: data.daily_cardio.map(d => d.total_duration),
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } }
    }
  });
}

async function renderCardioDistanceChart() {
  console.log("[INFO] Fetching cardio distance...");
  const data = await fetchJSON('/api/summary/cardio?days=7');
  const ctx = document.getElementById('cardioDistanceChart').getContext('2d');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.daily_cardio.map(d => d.date),
      datasets: [{
        label: 'Distance (mi)',
        data: data.daily_cardio.map(d => d.total_distance),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } }
    }
  });
}

async function renderStrengthChart() {
  console.log("[INFO] Fetching strength summary...");

  const data = await fetchJSON('/api/summary/strength?days=7');
  const summary = data.strength_summary || [];

  console.log("[DEBUG] Strength per-exercise summary:", summary);

  const canvas = document.getElementById('strengthSummaryChart');
  const ctx = canvas.getContext('2d');

  // Clean up previous chart instance
  if (canvas._chartInstance) {
    canvas._chartInstance.destroy();
  }

  const labels = summary.map(d => d.exercise);
  const values = summary.map(d => d.total_sets);

  // Adjust chart height based on data length (fallback to a minimal height if empty)
  const barHeight = 50;
  canvas.height = Math.max(summary.length * barHeight, 150);

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Total Sets',
        data: values,
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: false,
      maintainAspectRatio: false,
      animation: false,
      layout: { padding: 0 },
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          beginAtZero: true,
          title: { display: true, text: 'Total Sets' }
        },
        y: {
          title: { display: true, text: 'Exercise' },
          ticks: {
            autoSkip: false,
            color: labels.length ? '#000' : '#aaa'
          }
        }
      }
    }
  });

  canvas._chartInstance = chart;
}



async function renderPRList() {
  console.log("[INFO] Fetching PRs...");

  try {
    const res = await fetch('/api/summary/prs?days=7');
    if (!res.ok) throw new Error("Failed to fetch PRs");
    const data = await res.json();

    const list = document.getElementById('prList');
    const prs = data.prs || [];

    console.log("[DEBUG] PRs fetched:", prs);

    if (prs.length === 0) {
      list.innerHTML = `<li class="text-gray-500 text-sm">No PRs in the past 7 days.</li>`;
      return;
    }

    list.innerHTML = prs.map(pr => `
      <li>
        <span class="font-medium capitalize">${pr.exercise}</span> -
        <span class="text-blue-600 font-semibold">${pr.value}</span>
        <span class="text-gray-500 text-xs">(${pr.field}, ${pr.date})</span>
      </li>
    `).join('');
  } catch (err) {
    console.error("[ERROR] Failed to render PRs:", err);
    const list = document.getElementById('prList');
    list.innerHTML = `<li class="text-red-500 text-sm">Error loading PRs.</li>`;
  }
}


document.addEventListener('DOMContentLoaded', async () => {
  try {
    await Promise.all([
      renderSummaryStats(),
      renderCardioDurationChart(),
      renderCardioDistanceChart(),
      renderStrengthChart(),
      renderPRList()
    ]);
  } catch (err) {
    console.error('Error loading dashboard:', err);
  }
});

