import {tryGetCleanHref} from './defang.js';
import {make} from './dom.js';
import {forEach} from './util/array-like.js';
import loginName from './util/login-name.js';

const USER_LINK = /\\(.)|<(!~|[!~])(\w+)>|./gi;

const NO_USER_LINKING = ['A', 'PRE', 'CODE'];

// See `libweasyl.text._replace_bad_links`.
const replaceBadLinks = fragment => {
    // use `querySelectorAll` instead of `getElementsByTagName` to get a static node list
    const links = fragment.querySelectorAll('a');

    forEach(links, link => {
        const href = link.getAttribute('href');

        if (href !== null && tryGetCleanHref(href) === null) {
            link.replaceWith(make('span', {
                className: 'invalid-markup',
                title: 'invalid link',
                textContent: `${link.textContent} [${href}]`,
            }));
        }
    });
};

const addUserLinks = fragment => {
    for (let i = 0; i < fragment.childNodes.length; i++) {
        const child = fragment.childNodes[i];

        if (child.nodeType === 1) {
            if (!NO_USER_LINKING.includes(child.nodeName)) {
                addUserLinks(child);
            }
        } else if (child.nodeType === 3) {
            let text = '';
            let altered = false;

            for (let m; (m = USER_LINK.exec(child.nodeValue));) {
                if (m[1] !== undefined) {
                    text += m[1];
                    altered = true;
                    continue;
                }

                if (m[2] === undefined) {
                    text += m[0];
                    continue;
                }

                altered = true;

                const link = document.createElement('a');
                link.href = '/~' + loginName(m[3]);

                if (m[2] === '~') {
                    link.textContent = m[3];
                } else {
                    link.className = 'user-icon';

                    const image = document.createElement('img');
                    image.src = '/~' + loginName(m[3]) + '/avatar';
                    link.appendChild(image);

                    if (m[2] === '!') {
                        image.alt = m[3];
                    } else {
                        const usernameContainer = document.createElement('span');
                        usernameContainer.textContent = m[3];

                        link.appendChild(document.createTextNode(' '));
                        link.appendChild(usernameContainer);
                    }
                }

                fragment.insertBefore(document.createTextNode(text), child);
                fragment.insertBefore(link, child);
                text = '';
            }

            if (altered) {
                fragment.insertBefore(document.createTextNode(text), child);
                i = Array.prototype.indexOf.call(fragment.childNodes, child) - 1;
                fragment.removeChild(child);
            }
        }
    }
};

const weasylMarkdown = fragment => {
    const links = fragment.getElementsByTagName('a');

    forEach(links, link => {
        const href = link.getAttribute('href');
        const i = href.indexOf(':');
        const scheme = href.substring(0, i);
        const user = href.substring(i + 1);

        switch (scheme) {
            case 'user':
                link.href = '/~' + user;
                break;

            case 'da':
                link.href = 'https://www.deviantart.com/' + user;
                break;

            case 'sf':
                link.href = 'https://' + user + '.sofurry.com/';
                break;

            case 'ib':
                link.href = 'https://inkbunny.net/' + user;
                break;

            case 'fa':
                link.href = 'https://www.furaffinity.net/user/' + user;
                break;

            default:
                return;
        }

        if (!link.textContent || link.textContent === href) {
            link.textContent = user;
        }
    });

    const images = fragment.querySelectorAll('img');

    forEach(images, image => {
        const src = image.getAttribute('src');
        const i = src.indexOf(':');
        const scheme = src.substring(0, i);
        const link = document.createElement('a');

        if (scheme === 'user') {
            const user = src.substring(i + 1);
            image.className = 'user-icon';
            image.src = '/~' + user + '/avatar';

            link.href = '/~' + user;

            image.parentNode.replaceChild(link, image);
            link.appendChild(image);

            if (image.alt) {
                link.appendChild(document.createTextNode(' ' + image.alt));
                image.alt = '';
            } else {
                image.alt = user;
            }

            if (image.title) {
                link.title = image.title;
                image.title = '';
            }
        } else {
            link.href = image.src;
            link.appendChild(document.createTextNode(image.alt || image.src));

            image.parentNode.replaceChild(link, image);
        }
    });

    replaceBadLinks(fragment);

    addUserLinks(fragment);
};

export default weasylMarkdown;
