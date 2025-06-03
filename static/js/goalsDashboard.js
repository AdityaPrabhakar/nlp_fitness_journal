import { authFetch } from "./auth/authFetch.js";
import {renderGoalCard} from "./goalCard.js";

document.addEventListener('DOMContentLoaded', () => {
  fetchGoalsAndRender();

  document.getElementById('applyFilters').addEventListener('click', fetchGoalsAndRender);

  const dropdownBtn = document.getElementById('statusDropdownBtn');
  const dropdownMenu = document.getElementById('statusDropdown');
  dropdownBtn.addEventListener('click', () => {
    dropdownMenu.classList.toggle('hidden');
  });

  document.addEventListener('click', (e) => {
    if (!dropdownBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
      dropdownMenu.classList.add('hidden');
    }
  });

  createDeleteModal(); // Create modal once on load
});

async function fetchGoalsAndRender() {
  const container = document.getElementById('goals-container');
  if (!container) return;

  container.innerHTML = 'Loading...';

  try {
    const type = document.getElementById('goalTypeFilter').value;
    const exercise = document.getElementById('exerciseTypeFilter').value;
    const nameSearch = document.getElementById('exerciseNameFilter').value.toLowerCase();
    const startDate = document.getElementById('startDateFilter').value;
    const endDate = document.getElementById('endDateFilter').value;
    const statusCheckboxes = document.querySelectorAll('.statusOption:checked');
    const statusFilters = Array.from(statusCheckboxes).map(cb => cb.value);

    const res = await authFetch(`/api/goals/with-progress`);
    const data = await res.json();

    container.innerHTML = '';

    const filtered = data.filter(goal => {
      if (type && goal.goal_type !== type) return false;
      if (exercise && goal.exercise_type !== exercise) return false;
      if (nameSearch && !(goal.exercise_name || '').toLowerCase().includes(nameSearch)) return false;
      if (startDate && goal.start_date < startDate) return false;

      if (endDate) {
        if (goal.end_date && goal.end_date > endDate) return false;
        if (!goal.end_date) return false;
      }

      let status = goal.is_complete ? 'completed' : goal.is_expired ? 'expired' : 'in_progress';
      return statusFilters.includes(status);
    });

    if (!filtered.length) {
      container.innerHTML = '<p>No goals found.</p>';
      return;
    }

    filtered.forEach(goal => {
      const card = document.createElement('div');
      card.innerHTML = renderGoalCard(goal, { showDelete: true });
      container.appendChild(card);
    });



    document.querySelectorAll('.delete-goal-btn').forEach(button => {
      button.addEventListener('click', (e) => {
        const goalId = e.currentTarget.getAttribute('data-goal-id');
        showDeleteModal(goalId);
      });
    });

  } catch (err) {
    console.error('Error loading goals:', err);
    container.innerHTML = '<p class="text-red-600">Failed to load goals.</p>';
  }
}
// ----- Modal logic -----

function createDeleteModal() {
  const modal = document.createElement("div");
  modal.id = "deleteModal";
  modal.className = "fixed inset-0 z-50 hidden flex items-center justify-center bg-black/40";
  modal.innerHTML = `
    <div class="bg-white rounded-xl shadow-lg p-6 max-w-md w-full">
      <h2 class="text-lg font-semibold mb-4">Confirm Delete</h2>
      <p class="mb-6 text-sm text-gray-600">Are you sure you want to delete this goal? This action cannot be undone.</p>
      <div class="flex justify-end space-x-2">
        <button id="cancelDeleteBtn" class="px-4 py-2 text-sm rounded bg-gray-200 hover:bg-gray-300">Cancel</button>
        <button id="confirmDeleteBtn" class="px-4 py-2 text-sm rounded bg-red-500 text-white hover:bg-red-600">Delete</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

function showDeleteModal(goalId) {
  const modal = document.getElementById("deleteModal");
  modal.classList.remove("hidden");

  const cancelBtn = document.getElementById("cancelDeleteBtn");
  const confirmBtn = document.getElementById("confirmDeleteBtn");

  const closeModal = () => modal.classList.add("hidden");

  const handleConfirm = async () => {
    try {
      const res = await authFetch(`/api/goals/${goalId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error("Failed to delete goal");
      fetchGoalsAndRender();
    } catch (err) {
      console.error("Error deleting goal:", err);
      alert("There was a problem deleting the goal.");
    } finally {
      closeModal();
    }
  };

  cancelBtn.onclick = closeModal;
  confirmBtn.onclick = handleConfirm;
}
