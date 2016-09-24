'use strict';

module.exports = function remove(element) {
    element.parentNode.removeChild(element);
};
