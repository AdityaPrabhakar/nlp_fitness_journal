// modal.js
export function openModal(contentOrId, options = {}) {
    const modal = document.getElementById('session-modal');
    const sessionDetails = document.getElementById('session-details');

    if (!modal || !sessionDetails) return;

    // Remove old size classes
    const modalBox = modal.querySelector('.modal-box');
    modalBox.classList.remove('w-96', 'w-[600px]', 'w-[800px]', 'max-h-[80vh]');

    // Apply new size
    if (options.size === 'xl') {
        modalBox.classList.add('w-[800px]', 'max-h-[80vh]', 'overflow-y-auto');
    } else {
        modalBox.classList.add('w-96'); // default size
    }

    // Set content
    if (typeof contentOrId === 'string' && contentOrId.startsWith('#')) {
        const modalId = contentOrId.slice(1);
        document.getElementById(modalId)?.classList.remove('hidden');
    } else {
        sessionDetails.innerHTML = contentOrId;
        modal.classList.remove('hidden');
    }

    document.body.classList.add('overflow-hidden');
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

