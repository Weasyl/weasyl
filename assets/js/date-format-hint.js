'use strict';

var remove = require('./remove');

var supported = (function () {
    var input = document.createElement('input');
    input.type = 'date';
    return input.type === 'date';
})();

function setHintVisibility(container) {
    if (!supported) {
        return;
    }

    var hints = container.getElementsByClassName('date-format-hint');

    for (var i = 0; i < hints.length; i++) {
        remove(hints[i]);
    }
}

exports.setHintVisibility = setHintVisibility;
