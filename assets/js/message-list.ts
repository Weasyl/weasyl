
import {byClass, make} from './dom.js';

// ---------------------------------------------------------------------
// DOM elements
// ---------------------------------------------------------------------
const actionRemove = byClass('notes-action-remove', document) as HTMLButtonElement;
const notesList = byClass('notes-list', document) as HTMLElement; // container for note checkboxes
const selectAll = make('input', {
  type: 'checkbox',
  title: 'Select all on this page',
}) as HTMLInputElement;

// ---------------------------------------------------------------------
// State variables
// ---------------------------------------------------------------------
let checkedCount = 0; // number of checked notes
let totalCount = 0;   // total number of notes in the list

// ---------------------------------------------------------------------
// Initialise totalCount once the DOM is ready
// ---------------------------------------------------------------------
function initCounts(): void {
  const notes = notesList.querySelectorAll('[name=notes]');
  totalCount = notes.length;
}

// ---------------------------------------------------------------------
// Update UI based on current selection
// ---------------------------------------------------------------------
const updateSelection = (): void => {
  selectAll.checked = checkedCount === totalCount;
  selectAll.indeterminate = checkedCount > 0 && checkedCount < totalCount;
  actionRemove.disabled = checkedCount === 0;
  actionRemove.textContent = `Delete ${checkedCount} selected note${checkedCount === 1 ? '' : 's'}`;
};

// ---------------------------------------------------------------------
// Event handling for individual note checkboxes
// ---------------------------------------------------------------------
notesList.addEventListener('change', e => {
  const target = e.target as HTMLInputElement;
  if (target.name === 'notes') {
    checkedCount += target.checked ? 1 : -1;
    updateSelection();
  }
});

// ---------------------------------------------------------------------
// Initialise on load
// ---------------------------------------------------------------------
initCounts();
updateSelection();
