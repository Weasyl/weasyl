import {byClass, make} from './dom.js';
import {tryGetLocal, trySetLocal} from './util/storage.js';

var initEmbed = () => {
    var embedLink = byClass('embed-link');
    var service;
    if (!embedLink || !(service = embedLink.dataset.service)) {
        // no embed or embed failed to load
        return;
    }

    var embedContainer = embedLink.parentNode;

    var sourceName = embedLink.textContent.replace('View on ', '');

    var loadButton = make('button', {
        type: 'button',
        className: 'embed-load button',
        textContent: `Load ${sourceName}`,
    });

    var autoloadPreference = tryGetLocal(`embed-autoload-${service}`);

    var remember = make('input', {
        type: 'checkbox',
        checked: autoloadPreference !== 'n',
    });

    var rememberLabel = make('span');
    rememberLabel.append(`Always load embeds from ${sourceName} `, make('small', {textContent: 'in this browser'}));

    var controls = make('div', {className: 'embed-controls'});

    var load = () => {
        var frame = make('iframe', {className: 'embed-frame'});

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
