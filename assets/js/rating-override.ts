import {byId} from './dom.js';

// See `weasyl.controllers.detail.RATING_OVERRIDE_COOKIE`.
const RATING_OVERRIDE_COOKIE = 'ro';

const form = byId('rating-override');
if (!form) {
    return;
}

const submitid = Number(form.dataset.submitid);

form.addEventListener('submit', e => {
    e.preventDefault();

    document.cookie = `${RATING_OVERRIDE_COOKIE}=${submitid};max-age=${15 * 60};path=/;secure`;

    // Avoid creating extra history entries or overwriting forward history.
    const canonical = document.head.querySelector('link[rel="canonical"]');
    if (canonical) {
        location.replace(canonical.href);
    }
});

const viewAnyway = byId('view-anyway');
if (viewAnyway) {
    viewAnyway.disabled = false;
}

const ratingOverrideNoscript = byId('rating-override-noscript');
if (ratingOverrideNoscript) {
    ratingOverrideNoscript.remove();
}