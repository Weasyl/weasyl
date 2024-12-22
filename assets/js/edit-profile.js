let newSocialGroup = document.getElementById('new-social-group');

function markEntryForRemoval() {
    this.parentNode.parentNode.querySelectorAll('input')
        .forEach(element => element.disabled = true);

    this.textContent = '🔄';
    this.className.replace('negative', 'positive');
    this.removeEventListener('click', markEntryForRemoval);
    this.addEventListener('click', unmarkEntryForRemoval);
}

function unmarkEntryForRemoval() {
    this.parentNode.parentNode.querySelectorAll('input')
        .forEach(element => element.disabled = false);

    this.textContent = '🗑';
    this.className.replace('positive', 'negative');
    this.removeEventListener('click', unmarkEntryForRemoval);
    this.addEventListener('click', markEntryForRemoval);
}

function addNewSocialGroupIfNeeded() {
    if (this.querySelectorAll('input[value]')) {
        newSocialGroup = this.cloneNode(true);
        newSocialGroup.querySelectorAll('input').forEach(element => element.value = '');
        this.querySelector('.remove-contact').hidden = false;
        this.removeAttribute('id');
        this.insertAdjacentElement('afterend', newSocialGroup);
        this.removeEventListener('input', addNewSocialGroupIfNeeded);
        newSocialGroup.addEventListener('input', addNewSocialGroupIfNeeded);
    }
}

newSocialGroup.addEventListener('input', addNewSocialGroupIfNeeded);

document
    .querySelectorAll('tr:not(#new-social-group) .remove-contact')
    .forEach(element => {
        element.hidden = false;
        element.firstChild.addEventListener('click', markEntryForRemoval);
    });
