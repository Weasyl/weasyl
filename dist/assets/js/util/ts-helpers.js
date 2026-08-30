// Utility helpers for safe type casting and conversions in the project
export function toNumber(value) {
    const num = Number(value);
    if (Number.isNaN(num)) {
        throw new Error(`Unable to convert ${value} to number`);
    }
    return num;
}
export function asHTMLInputElement(el) {
    if (el instanceof HTMLInputElement)
        return el;
    throw new Error('Element is not an HTMLInputElement');
}
export function asHTMLDivElement(el) {
    if (el instanceof HTMLDivElement)
        return el;
    throw new Error('Element is not an HTMLDivElement');
}
export function asHTMLElement(el) {
    if (el instanceof HTMLElement)
        return el;
    throw new Error('Element is not an HTMLElement');
}
export function asHTMLAnchorElement(el) {
    if (el instanceof HTMLAnchorElement)
        return el;
    throw new Error('Element is not an HTMLAnchorElement');
}
