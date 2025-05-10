export var byClass = (class_, within) =>
    (within ?? document).getElementsByClassName(class_)[0];

export var make = (element, props) =>
    Object.assign(document.createElement(element), props);
