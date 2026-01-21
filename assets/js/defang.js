const allowedTags = new Set([
    'SECTION', 'NAV', 'ARTICLE', 'ASIDE',
    'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
    'HEADER', 'FOOTER', 'ADDRESS',
    'P', 'HR', 'PRE', 'BLOCKQUOTE', 'OL', 'UL', 'LI',
    'DL', 'DT', 'DD', 'FIGURE', 'FIGCAPTION', 'DIV',
    'EM', 'STRONG', 'SMALL', 'S', 'CITE', 'Q', 'DFN',
    'ABBR', 'TIME', 'CODE', 'VAR', 'SAMP', 'KBD',
    'SUB', 'SUP', 'I', 'B', 'U', 'MARK',
    'RUBY', 'RT', 'RP', 'BDI', 'BDO', 'SPAN', 'BR', 'WBR',
    'DEL',
    'TABLE', 'CAPTION',
    'TBODY', 'THEAD', 'TFOOT', 'TR', 'TD', 'TH',
    'A', 'IMG',
]);

const allowedAttributes = new Set([
    'title', 'alt', 'colspan', 'rowspan', 'start', 'type',
]);

const allowedSchemes = new Set([
    'http:', 'https:', 'mailto:', 'irc:', 'ircs:', 'magnet:',
]);

const allowedClasses = new Set([
    'align-left', 'align-center', 'align-right', 'align-justify',
    'user-icon',
    'invalid-markup',
]);

const ALLOWED_STYLE = /^\s*color:\s*(?:#[0-9a-f]{3}|#[0-9a-f]{6})(?:\s*;)?\s*$/i;

const DUMMY_URL_BASE = 'https://h/';

// See `libweasyl.defang.CleanHref`.
export const tryGetCleanHref = s => {
    // deno-lint-ignore no-control-regex
    s = s.replace(/^[\x00-\x20]+|[\t\n\r]/g, '');

    let u;

    try {
        u = new URL(s);
    } catch {
        u = null;
    }

    if (u !== null) {
        return allowedSchemes.has(u.protocol) ? u.href : null;
    }

    if (!/^[\/\\]/.test(s)) {
        return null;
    }

    try {
        u = new URL(s, DUMMY_URL_BASE);
    } catch {
        return null;
    }

    if (/^[\/\\]{2}/.test(s)) {
        return u.href;
    }

    return u.pathname;
};

const defang = (node, isBody) => {
    for (let i = node.childNodes.length; i--;) {
        const child = node.childNodes[i];

        if (child.nodeType === 1) {
            defang(child, false);
        }
    }

    if (!isBody && !allowedTags.has(node.nodeName)) {
        while (node.hasChildNodes()) {
            node.parentNode.insertBefore(node.firstChild, node);
        }

        node.parentNode.removeChild(node);
    } else {
        for (let i = node.attributes.length; i--;) {
            const attribute = node.attributes[i];
            let cleanHref;

            if (node.nodeName === 'A' && attribute.name === 'href' && (cleanHref = tryGetCleanHref(attribute.value)) !== null) {
                attribute.value = cleanHref;
                continue;
            }

            if (node.nodeName === 'IMG' && attribute.name === 'src' && (cleanHref = tryGetCleanHref(attribute.value)) !== null) {
                attribute.value = cleanHref;
                continue;
            }

            if (attribute.name === 'style' && ALLOWED_STYLE.test(attribute.value)) {
                continue;
            }

            if (attribute.name === 'class') {
                const classes = attribute.value.split(/\s+/);

                attribute.value = classes.filter(allowedClasses.has, allowedClasses).join(' ');

                if (attribute.value) {
                    continue;
                }
            }

            if (allowedAttributes.has(attribute.name)) {
                continue;
            }

            node.removeAttribute(attribute.name);
        }
    }
};

export default defang;
