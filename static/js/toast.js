// ---- Toast creation logic inline ---- //
export function showPRToast(prs) {
    const container = document.createElement('div');
    container.className = 'fixed top-4 right-4 z-50 flex flex-col gap-2';
    container.id = 'pr-toast-container';

    prs.forEach(pr => {
        const toast = document.createElement('div');
        toast.className = 'bg-green-600 text-white px-4 py-2 rounded shadow-lg transition-opacity duration-500';

        let message = `🎉 New PR: ${pr.exercise} — `;

        if (pr.type === 'strength') {
            if (pr.field === 'weight') {
                message += `${pr.value} lbs`;
            } else if (pr.field === 'reps') {
                message += `${pr.value} reps`;
            }
        } else if (pr.type === 'cardio') {
            if (pr.field === 'distance') {
                message += `${pr.value} mi`;
            } else if (pr.field === 'duration') {
                message += `${pr.value} min`;
            }
        }

        toast.innerText = message;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 500);
        }, 4000);
    });

    const existing = document.getElementById('pr-toast-container');
    if (existing) existing.remove();

    document.body.appendChild(container);
}