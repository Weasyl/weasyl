import parseTags from './parse-tags.js';

const element = document.querySelector('[name="tags"]');

element.addEventListener('change', () => {
    const tags = new Set(parseTags(element.value));

    if (tags.size < 2) {
        element.setCustomValidity('Please enter at least two unique tags.');
    } else {
        element.setCustomValidity('');
    }
});
