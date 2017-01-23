'use strict';

var forEach = Array.prototype.forEach;
var every = Array.prototype.every;
var some = Array.prototype.some;
var map = Array.prototype.map;

var notificationContainer = document.getElementById('messages-checkboxes');
var notificationGlobalActions = document.getElementById('notification-global-actions');
var notificationGlobalActionsTop = document.getElementById('notification-global-actions-top');
var removeCheckedButton = document.getElementById('remove-checked');
var removeCheckedButtonTop = document.getElementById('remove-checked-top');
var sectionHeaders = notificationContainer.getElementsByClassName('notification-group-header');
var removeCheckboxes = notificationContainer.getElementsByClassName('remove');

function isChecked(checkbox) {
    return checkbox.checked;
}

function sectionToggle(section) {
    var itemCheckboxes = section.getElementsByClassName('remove');
    var sectionCheckbox = document.createElement('input');

    sectionCheckbox.type = 'checkbox';

    function updateItemCheckboxes() {
        var checked = sectionCheckbox.checked;

        forEach.call(itemCheckboxes, function (checkbox) {
            checkbox.checked = checked;
            checkbox.parentNode.classList.toggle('checked', checked);
        });

        updateRemoveChecked();
    }

    function updateSectionCheckbox() {
        sectionCheckbox.checked = every.call(itemCheckboxes, isChecked);
    }

    sectionCheckbox.addEventListener('change', updateItemCheckboxes);
    section.addEventListener('change', updateSectionCheckbox);
    updateSectionCheckbox();

    return sectionCheckbox;
}

var sectionCheckboxes = map.call(sectionHeaders, function (sectionHeader) {
    var label = document.createElement('label');
    var sectionCheckbox = sectionToggle(sectionHeader.nextElementSibling);

    label.appendChild(sectionCheckbox);
    label.appendChild(document.createTextNode(' '));
    label.appendChild(sectionHeader.firstChild);

    sectionHeader.appendChild(label);

    return sectionCheckbox;
});

function checkAllButton(text, checked) {
    var button = document.createElement('button');

    button.type = 'button';
    button.className = checked ? 'button notifs-check-all' : 'button notifs-uncheck-all';
    button.textContent = text;

    button.addEventListener('click', function () {
        forEach.call(removeCheckboxes, function (checkbox) {
            checkbox.checked = checked;
            checkbox.parentNode.classList.toggle('checked', checked);
        });

        sectionCheckboxes.forEach(function (checkbox) {
            checkbox.checked = checked;
        });

        removeCheckedButton.disabled = !checked;
        removeCheckedButtonTop.disabled = !checked;
    });

    return button;
}

function updateRemoveChecked() {
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
