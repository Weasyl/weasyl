import {byClass, make} from './dom.js';
import {tryGetLocal, trySetLocal} from './util/storage.js';

const initEmbed = () => {
    const embedLink = byClass('embed-link');
    let service;
    if (!embedLink || !(service = embedLink.dataset.service)) {
        // no embed or embed failed to load
        return;
    }

    const embedContainer = embedLink.parentNode;

    const sourceName = embedLink.textContent.replace('View on ', '');

    const loadButton = make('button', {
        type: 'button',
        className: 'embed-load button',
        textContent: `Load ${sourceName}`,
    });

    const autoloadPreference = tryGetLocal(`embed-autoload-${service}`);

    const remember = make('input', {
        type: 'checkbox',
        checked: autoloadPreference !== 'n',
    });

    const rememberLabel = make('span');
    rememberLabel.append(`Always load embeds from ${sourceName} `, make('small', {textContent: 'in this browser'}));

    const controls = make('div', {className: 'embed-controls'});

    const load = () => {
        const frame = make('iframe', {className: 'embed-frame'});

        if (service === 'bandcamp') {
            frame.src = `https://bandcamp.com/EmbeddedPlayer/${embedLink.dataset.bandcampId}/size=large/bgcol=ffffff/linkcol=0687f5/tracklist=false/artwork=small/transparent=true/`;
        } else {
            frame.srcdoc = '<!DOCTYPE html><style>html,body{height:100%;margin:0}iframe{display:block;border:0;width:100%}</style><body>' + embedLink.dataset.untrustedHtml;
        }
        // no `sandbox` intentionally; different origin is enough for these trusted services, and almost all permissions are appropriate for them (top-level navigation, fullscreen, etc.)

        embedContainer.textContent = '';
        embedContainer.append(frame);
    };

    loadButton.addEventListener('click', () => {
        load();
        trySetLocal(`embed-autoload-${service}`, remember.checked ? 'y' : 'n');
    });

    embedLink.replaceWith(controls);
    embedLink.classList.remove('button');
    controls.append(loadButton, embedLink);
    controls.appendChild(make('label', {className: 'embed-remember'})).append(remember, rememberLabel);

    if (autoloadPreference === 'y') {
        load();
    }
};

export default initEmbed;
