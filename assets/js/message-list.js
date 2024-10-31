import {byClass, make} from './dom.js';

const notesList = byClass('notes-list');
const actionRemove = byClass('notes-action-remove');
const totalCount = document.getElementsByName('notes').length;
let checkedCount = notesList.querySelectorAll('[name=notes]:checked').length;
const selectAll = make('input', {
    type: 'checkbox',
    title: 'Select all on this page',
});

const updateSelection = () => {
    selectAll.checked = checkedCount === totalCount;
    selectAll.indeterminate = checkedCount > 0 && checkedCount < totalCount;
    actionRemove.disabled = checkedCount === 0;
    actionRemove.textContent = `Delete ${checkedCount} selected note${checkedCount === 1 ? '' : 's'}`;
};

selectAll.addEventListener('change', () => {
    checkedCount = 0;

    for (const noteSelect of document.getElementsByName('notes')) {
        checkedCount += (noteSelect.checked = selectAll.checked);
    }

    updateSelection();
});

notesList.addEventListener('change', e => {
    if (e.target.name === 'notes') {
        checkedCount += e.target.checked ? 1 : -1;
        updateSelection();
    }
});

updateSelection();

if (!byClass('notes-empty')) {
    byClass('notes-select-all').append(selectAll);
}
