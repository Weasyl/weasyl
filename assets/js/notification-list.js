const forEach = Array.prototype.forEach;
const every = Array.prototype.every;
const some = Array.prototype.some;
const map = Array.prototype.map;

const notificationContainer = document.getElementById('messages-checkboxes');
const notificationGlobalActions = document.getElementById('notification-global-actions');
const notificationGlobalActionsTop = document.getElementById('notification-global-actions-top');
const removeCheckedButton = document.getElementById('remove-checked');
const removeCheckedButtonTop = document.getElementById('remove-checked-top');
const sectionHeaders = notificationContainer.getElementsByClassName('notification-group-header');
const removeCheckboxes = notificationContainer.getElementsByClassName('remove');

const isChecked = checkbox => {
    return checkbox.checked;
}

const sectionToggle = section => {
    const itemCheckboxes = section.getElementsByClassName('remove');
    const sectionCheckbox = document.createElement('input');

    sectionCheckbox.type = 'checkbox';

    const updateItemCheckboxes = () => {
        const checked = sectionCheckbox.checked;

        forEach.call(itemCheckboxes, checkbox => {
            checkbox.checked = checked;
            checkbox.parentNode.classList.toggle('checked', checked);
        });

        updateRemoveChecked();
    }

    const updateSectionCheckbox = () => {
        sectionCheckbox.checked = every.call(itemCheckboxes, isChecked);
    }

    sectionCheckbox.addEventListener('change', updateItemCheckboxes);
    section.addEventListener('change', updateSectionCheckbox);
    updateSectionCheckbox();

    return sectionCheckbox;
}

const sectionCheckboxes = map.call(sectionHeaders, sectionHeader => {
    const label = document.createElement('label');
    const sectionCheckbox = sectionToggle(sectionHeader.nextElementSibling);

    label.appendChild(sectionCheckbox);
    label.appendChild(document.createTextNode(' '));
    label.appendChild(sectionHeader.firstChild);

    sectionHeader.appendChild(label);

    return sectionCheckbox;
});

const checkAllButton = (text, checked) => {
    const button = document.createElement('button');

    button.type = 'button';
    button.className = checked ? 'button notifs-check-all' : 'button notifs-uncheck-all';
    button.textContent = text;

    button.addEventListener('click', () => {
        forEach.call(removeCheckboxes, checkbox => {
            checkbox.checked = checked;
            checkbox.parentNode.classList.toggle('checked', checked);
        });

        sectionCheckboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });

        removeCheckedButton.disabled = !checked;
        removeCheckedButtonTop.disabled = !checked;
    });

    return button;
}

const updateRemoveChecked = () => {
    removeCheckedButton.disabled = !some.call(removeCheckboxes, isChecked);
    removeCheckedButtonTop.disabled = !some.call(removeCheckboxes, isChecked);
}

notificationContainer.addEventListener('change', updateRemoveChecked);
updateRemoveChecked();

notificationGlobalActions.insertBefore(checkAllButton('Uncheck All', false), notificationGlobalActions.firstChild);
notificationGlobalActions.insertBefore(document.createTextNode(' '), notificationGlobalActions.firstChild);
notificationGlobalActions.insertBefore(checkAllButton('Check All', true), notificationGlobalActions.firstChild);

notificationGlobalActionsTop.insertBefore(checkAllButton('Uncheck All', false), notificationGlobalActionsTop.firstChild);
notificationGlobalActionsTop.insertBefore(document.createTextNode(' '), notificationGlobalActionsTop.firstChild);
notificationGlobalActionsTop.insertBefore(checkAllButton('Check All', true), notificationGlobalActionsTop.firstChild);
