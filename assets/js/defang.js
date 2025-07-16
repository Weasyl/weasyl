const allowedTags = new Set([
    'section', 'nav', 'article', 'aside',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'header', 'footer', 'address',
    'p', 'hr', 'pre', 'blockquote', 'ol', 'ul', 'li',
    'dl', 'dt', 'dd', 'figure', 'figcaption', 'div',
    'em', 'strong', 'small', 's', 'cite', 'q', 'dfn',
    'abbr', 'time', 'code', 'var', 'samp', 'kbd',
    'sub', 'sup', 'i', 'b', 'u', 'mark',
    'ruby', 'rt', 'rp', 'bdi', 'bdo', 'span', 'br', 'wbr',
    'del',
    'table', 'caption',
    'tbody', 'thead', 'tfoot', 'tr', 'td', 'th',
    'a', 'img',
]);

const allowedAttributes = new Set([
    'title', 'alt', 'colspan', 'rowspan', 'start', 'type',
]);

const allowedSchemes = new Set([
    '', 'http', 'https', 'mailto', 'irc', 'magnet',
]);

const allowedClasses = new Set([
    'align-left', 'align-center', 'align-right', 'align-justify',
    'user-icon',
]);

const ALLOWED_STYLE = /^\s*color:\s*(?:#[0-9a-f]{3}|#[0-9a-f]{6})(?:\s*;)?\s*$/i;

const defang = (node, isBody) => {
    for (let i = node.childNodes.length; i--;) {
        const child = node.childNodes[i];

        if (child.nodeType === 1) {
            defang(child, false);
        }
    }

    if (!isBody && !allowedTags.has(node.nodeName.toLowerCase())) {
        while (node.hasChildNodes()) {
            node.parentNode.insertBefore(node.firstChild, node);
        }

        node.parentNode.removeChild(node);
    } else {
        for (let i = node.attributes.length; i--;) {
            const attribute = node.attributes[i];
            const scheme = attribute.value && attribute.value.substring(0, attribute.value.indexOf(':'));

            if (node.nodeName === 'A' && attribute.name === 'href' && allowedSchemes.has(scheme)) {
                continue;
            }

            if (node.nodeName === 'IMG' && attribute.name === 'src' && allowedSchemes.has(scheme)) {
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
