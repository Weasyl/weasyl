// `invalid-use-title` indicates that an element’s title is a good custom error message for when it doesn’t pass HTML form validation.
for (const element of document.getElementsByClassName('invalid-use-title')) {
    const message = element.title;
    element.title = '';

    const updateCustomValidity = () => {
        element.setCustomValidity('');

        if (!element.checkValidity()) {
            element.setCustomValidity(message);
        }
    };

    element.addEventListener('change', updateCustomValidity);
    updateCustomValidity();
}
