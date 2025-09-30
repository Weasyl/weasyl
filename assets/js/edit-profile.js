let newSocialGroup = document.getElementById('new-social-group');

function checkSuspiciousSiteName() {
    for (const prefix of ['http://', 'https://', 'mailto:']) {
        if (this.value.startsWith(prefix)) {
            // Only give a warning if one of these prefixes is detected, in
            // case a site exists in the future whose name literally starts
            // with a URL scheme. Given how many sites exist whose names end
            // with a top-level domain (currently .io, previously .com), better
            // to keep this optional just in case borrowing the beginning of
            // a URL comes into style in the future.
            this.setCustomValidity('Did you mean to place this in the URL field?');
            this.reportValidity();

            return;
        }
    }

    this.setCustomValidity('');
}

function markEntryForRemoval() {
    this.parentNode.parentNode.querySelectorAll('input').forEach(element => {
        element.disabled = true;
    });

    this.textContent = '⎌';
    this.title = 'Undo';
    this.classList.remove('negative');
    this.classList.add('positive');
    this.removeEventListener('click', markEntryForRemoval);
    this.addEventListener('click', unmarkEntryForRemoval);
}

function unmarkEntryForRemoval() {
    this.parentNode.parentNode.querySelectorAll('input').forEach(element => {
        element.disabled = false;
    });

    this.textContent = '❌';
    this.title = 'Remove';
    this.classList.remove('positive');
    this.classList.add('negative');
    this.removeEventListener('click', unmarkEntryForRemoval);
    this.addEventListener('click', markEntryForRemoval);
}

function addNewSocialGroupIfNeeded() {
    if (this.querySelectorAll('input[value]')) {
        newSocialGroup = this.cloneNode(true);

        newSocialGroup.querySelectorAll('input').forEach(element => {
            element.value = '';
        });

        newSocialGroup.querySelector('div[popover]').remove();

        const newSiteNameInput = newSocialGroup.querySelector('input[name="site_names"]');
        newSiteNameInput.setAttribute('list', 'known-social-sites');
        newSiteNameInput.addEventListener('input', checkSuspiciousSiteName);

        const removeContact = this.querySelector('.remove-contact');
        removeContact.hidden = false;
        removeContact.firstChild.addEventListener('click', markEntryForRemoval);

        this.removeAttribute('id');
        this.insertAdjacentElement('afterend', newSocialGroup);
        this.removeEventListener('input', addNewSocialGroupIfNeeded);
        newSocialGroup.addEventListener('input', addNewSocialGroupIfNeeded);
    }
}

newSocialGroup.addEventListener('input', addNewSocialGroupIfNeeded);

document.querySelector('th.remove-contact').hidden = false;

document.querySelectorAll('tr:not(#new-social-group) td.remove-contact').forEach(element => {
    element.hidden = false;
    element.firstChild.addEventListener('click', markEntryForRemoval);
});

document.querySelectorAll('input[name="site_names"]').forEach(element => {
    element.addEventListener('input', checkSuspiciousSiteName);
});
