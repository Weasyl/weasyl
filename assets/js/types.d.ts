
/* eslint-disable */

declare var marked: any;
declare var MARKED_SRC: string;
declare var Sanitizer: any;
declare module 'autosize' {
  const autosize: any;
  export default autosize;
}
declare module 'imgareaselect' {
  const imgAreaSelect: any;
  export default imgAreaSelect;
}

declare function zxcvbn(pwd: string): any;

declare global {
  interface HTMLElement {
    [key: string]: any;
  }
  interface EventTarget {
    [key: string]: any;
  }
}
declare global {
  interface JQuery {
    imgAreaSelect?(options?: any): JQuery;
  }
  interface JQueryStatic {
    imgAreaSelect?(options?: any): any;
  }
}
declare function fetch(input: RequestInfo, init?: any): Promise<Response>;

interface Document {
  parseHTML(html: string): Document;
  parseHTMLUnsafe(html: string): Document;
}

interface NodeListOf<T> {
  [Symbol.iterator](): IterableIterator<T>;
}

