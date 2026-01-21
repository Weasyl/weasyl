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

    // 200 indicates view count was incremented; 204 indicates it wasn't (or isn't visible either way); errors are ignored
    if (response.status === 200) {
        // NOTE: `viewsContainer` can be an empty `<script type="text/plain">` here (hidden user statistics that are reconfigured to visible between page load and `visible` resolving), but incrementing that invisible text to 1 is harmless
        viewsContainer.textContent++;
    }
});

export {}
