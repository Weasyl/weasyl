const getSearchTag = (text) =>
    text.replace(/[^ \w]/g, '')
        .toLowerCase()
        .match(/[0-9a-z]+/g)
        ?.join('_');

const parseTags = (s) =>
    s.split(/[\s,]+/)
        .map(getSearchTag)
        .filter(Boolean);

export default parseTags;
