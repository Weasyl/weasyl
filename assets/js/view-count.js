import ready from './util/ready.js';

const visible = new Promise(resolve => {
    const check = () => {
        if (!document.hidden) {
            document.removeEventListener('visibilitychange', check);
            resolve();
        }
    };

    document.addEventListener('visibilitychange', check);
    check();
});

visible.then(async () => {
    await ready;

    const viewsContainer = document.getElementById('page-views');

    if (!viewsContainer) {
        return;
    }

    if (new URLSearchParams('?' + location.search).get('anyway') === 'true') {
        return;
    }

    const response = await fetch(`/api-unstable/${viewsContainer.dataset.viewable}/views/`, {
        method: 'POST',
        priority: 'low',
        keepalive: true,
    });

    const updatedViews = await response.text();

    if (response.ok && updatedViews) {
        viewsContainer.textContent = updatedViews;
    }
});

export {}
