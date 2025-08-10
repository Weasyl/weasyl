export const byId = id =>
    document.getElementById(id);

export const byClass = (class_, within) =>
    (within ?? document).getElementsByClassName(class_)[0];

export const make = (element, props) =>
    Object.assign(document.createElement(element), props);
