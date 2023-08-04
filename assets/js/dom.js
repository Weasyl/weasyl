export const byClass = (class_, within = document) =>
    within.getElementsByClassName(class_)[0];

export const make = (element, props) =>
    Object.assign(document.createElement(element), props);
