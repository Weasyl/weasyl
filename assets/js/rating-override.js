import {byId} from './dom.js';

/// See `weasyl.controllers.detail.RATING_OVERRIDE_COOKIE`.
const RATING_OVERRIDE_COOKIE = 'ro';

const form = byId('rating-override');
const submitid = Number(form.dataset.submitid);

form.addEventListener('submit', e => {
    e.preventDefault();

    document.cookie = `${RATING_OVERRIDE_COOKIE}=${submitid};max-age=${15 * 60};path=/;secure`;

    // Avoid creating extra history entries or overwriting forward history.
    location.replace(document.head.querySelector('link[rel="canonical"]').href);
});

byId('view-anyway').disabled = false;
byId('rating-override-noscript').remove();
