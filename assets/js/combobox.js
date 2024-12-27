class Combobox extends HTMLInputElement {
    #list;
    #popover;

    constructor() {
        super();

        this.#popover = document.createElement('div');
    }

    connectedCallback() {
        this.#list = this.list; // disconnect datalist later, but keep reference

        // Temporarily remove `transition` to prevent the site name from
        // sliding toward the right on page load. `padding-left` gets set in
        // here instead of in the stylesheet to prevent the non-JS fallback
        // component from having text shifted for an icon that won't exist.
        this.style.transition = 'none';
        this.style.paddingLeft = '2em';

        this.style.backgroundImage = `url(${this.list.dataset.defaultImgSrc})`;

        this.#popover.setAttribute('popover', '');

        const list = document.createElement('ul');
        this.#popover.appendChild(list);

        for (const option of this.list.children) {
            const item = document.createElement('li');

            const icon = document.createElement('img');
            icon.src = option.dataset.imgSrc ?? this.list.dataset.defaultImgSrc;
            item.append(icon, option.value);

            item.addEventListener('click', event => {
                this.value = item.innerText;

                // Make sure a new, empty contact link entry always gets added.
                this.dispatchEvent(new Event('input', { bubbles: true }));
            });

            list.appendChild(item);
        }

        this.removeAttribute('list');
        this.after(this.#popover);

        for (const type of ['click', 'input']) {
            this.addEventListener(type, event => {
                this.#update();
            });
        }

        this.#update(false);
        this.style.transition = '';
    }

    #update(showPopover = true) {
        const rect = this.getBoundingClientRect();
        const top = rect.top + window.scrollY + rect.height;
        const left = rect.left + window.scrollX;

        this.#popover.style.top = `${top}px`;
        this.#popover.style.left = `${left}px`;
        this.#popover.style.maxHeight = `${rect.height * 6.7}px`;
        this.#popover.style.minWidth = `${rect.width}px`;

        const items = this.#popover.querySelectorAll('li');
        this.style.backgroundImage = `url(${this.#list.dataset.defaultImgSrc})`;

        for (const item of items) {
            item.hidden =
                !item.innerText.toLowerCase().startsWith(this.value.toLowerCase())
                || item.innerText === this.value;

            if (item.innerText === this.value) {
                this.style.backgroundImage = `url(${item.firstChild.src})`;
            }
        }

        if (!showPopover || Array.from(items).every(element => element.hidden)) {
            this.#popover.hidePopover();
        } else {
            this.#popover.showPopover();
        }
    }
}

const defineCombobox = () => {
    customElements.define('weasyl-combobox', Combobox, { extends: 'input' });
}

export default defineCombobox;
