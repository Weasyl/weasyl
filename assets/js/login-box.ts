
import {byId} from './dom.js';
import hasModifierKeys from './util/has-modifier-keys.js';

const loginTop = byId('login-top')!;

byId('hg-login').addEventListener('click', ev => {
    if (hasModifierKeys(ev)) {
        return;
    }

    if (loginTop) {
        loginTop.showModal();
    }
    ev.preventDefault();
});

byId('lb-close').addEventListener('click', () => {
    if (loginTop) {
        loginTop.close();
    }
});


