// modal.js

export function openModal(contentOrId) {
    const modal = document.getElementById('session-modal');
    const sessionDetails = document.getElementById('session-details');

    if (!modal || !sessionDetails) return;

    // If it's just an ID, assume modal already has content
    if (typeof contentOrId === 'string' && contentOrId.startsWith('#')) {
        const modalId = contentOrId.slice(1);
        document.getElementById(modalId)?.classList.remove('hidden');
    } else {
        sessionDetails.innerHTML = contentOrId;
        modal.classList.remove('hidden');
    }

    document.body.classList.add('overflow-hidden'); // Optional: prevent background scroll
}

export function closeModal() {
    const modal = document.getElementById('session-modal');
    if (!modal) return;

    modal.classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
}

export function setupModalTriggers() {
    // Open modal buttons
    document.querySelectorAll('button[data-modal]').forEach(button => {
        button.addEventListener('click', () => {
            const modalId = button.getAttribute('data-modal');
            const modal = document.getElementById(modalId);
            if (modal) modal.classList.remove('hidden');
        });
    });

    // Close modal on background click or .close-modal class
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', event => {
            if (event.target.classList.contains('modal-overlay')) {
                overlay.classList.add('hidden');
                document.body.classList.remove('overflow-hidden');
            }
        });
    });

    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', () => {
            button.closest('.modal-overlay')?.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        });
    });
}
