
import { TextEncoder, TextDecoder } from 'util';
Object.assign(global, { TextEncoder, TextDecoder });

describe('message-list module', () => {
  beforeEach(() => {
    // Use Jest's built-in jsdom document
    document.body.innerHTML = `
      <div class="notes-list">
        <input type="checkbox" name="notes" value="1" />
        <input type="checkbox" name="notes" value="2" />
      </div>
      <button class="notes-action-remove"></button>
    `;
    
    // Clear module cache to re-evaluate the module against the fresh DOM
    jest.resetModules();
    require('../../../assets/js/message-list.ts');
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  test('initial UI state reflects zero selected notes', () => {
    const actionRemove = document.querySelector('.notes-action-remove') as HTMLButtonElement;

    expect(actionRemove).not.toBeNull();
    // Initially no notes are checked, so button should be disabled and text show 0
    expect(actionRemove.disabled).toBeTruthy();
    expect(actionRemove.textContent).toContain('Delete 0');
  });

  test('checking a note updates UI', () => {
    const checkboxes = document.querySelectorAll('input[name=notes]') as any;
    const actionRemove = document.querySelector('.notes-action-remove') as HTMLButtonElement;

    // Simulate checking the first checkbox
    checkboxes[0].checked = true;
    const changeEvent = new window.Event('change', { bubbles: true });
    checkboxes[0].dispatchEvent(changeEvent);

    expect(actionRemove.disabled).toBeFalsy();
    expect(actionRemove.textContent).toContain('Delete 1');
  });
});
