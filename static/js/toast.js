export function showPRToast(prs) {
    const container = document.createElement('div');
    container.className = 'fixed top-4 right-4 z-50 flex flex-col gap-2';
    container.id = 'pr-toast-container';

    prs.forEach(pr => {
        const toast = document.createElement('div');
        toast.className = 'bg-green-600 text-white px-4 py-2 rounded shadow-lg transition-opacity duration-500';

        let message = `🎉 New PR: ${pr.exercise} — `;

        if (pr.field === 'pace' && pr.units === 'min/mi') {
            const minutes = Math.floor(pr.value);
            const seconds = Math.round((pr.value - minutes) * 60);
            const secondsStr = seconds < 10 ? `0${seconds}` : `${seconds}`;
            message += `${minutes}:${secondsStr} ${pr.units}`;
        } else {
            const value = typeof pr.value === 'number' ?
                (pr.units === 'mi' ? pr.value.toFixed(2) :
                 pr.units === 'min' || pr.units === 'lbs' ? pr.value.toFixed(1) :
                 pr.value)
                : pr.value;
            message += `${value} ${pr.units}`;
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
