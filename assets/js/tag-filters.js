let newBlockedTag = document.getElementById('new-blocked-tag');

const cloneWhenNonempty = e => {
    const target = e.currentTarget;

    if (target.value) {
        newBlockedTag = target.cloneNode(true);
        newBlockedTag.value = '';
        target.insertAdjacentElement('afterend', newBlockedTag);
        target.removeEventListener('input', cloneWhenNonempty);
        newBlockedTag.addEventListener('input', cloneWhenNonempty);
    }
}

newBlockedTag.addEventListener('input', cloneWhenNonempty);
