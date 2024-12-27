class Combobox extends HTMLInputElement {
    #list;
    #popover = document.createElement('div');
    #previousLeaveX = 0;
    #previousLeaveY = 0;
    #previousOverX = 0;
    #previousOverY = 0;

    constructor() {
        super();
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

        this.role = 'combobox';
        this.ariaControlsElements = [ this.#popover ];
        this.ariaAutoComplete = 'list';
        this.#popover.role = 'listbox';

        this.#popover.addEventListener('toggle', event => {
            this.ariaExpanded = event.newState === 'open';
        })

        for (const option of this.list.children) {
            const item = document.createElement('li');

            const icon = document.createElement('img');
            icon.src = option.dataset.imgSrc ?? this.list.dataset.defaultImgSrc;
            item.append(icon, option.value);

            item.ariaSelected = false;

            item.addEventListener('click', event => {
                this.value = item.innerText;

                // Make sure a new, empty contact link entry always gets added.
                this.dispatchEvent(new Event('input', { bubbles: true }));
            });

            item.addEventListener('mouseleave', event => {
                if (event.screenX === this.#previousLeaveX && event.screenY === this.#previousLeaveY) {
                    return;
                }

                this.#previousLeaveX = event.screenX;
                this.#previousLeaveY = event.screenY;

                item.ariaSelected = false;
                this.#popover.querySelector('.focus')?.classList.remove('focus');
                item.classList.remove('focus');
            });

            item.addEventListener('mouseover', event => {
                if (event.screenX === this.#previousOverX && event.screenY === this.#previousOverY) {
                    return;
                }

                this.#previousOverX = event.screenX;
                this.#previousOverY = event.screenY;

                item.ariaSelected = true;
                this.#popover.querySelector('.focus')?.classList.remove('focus');
                item.classList.add('focus');
            });

            item.addEventListener('blur', event => {
                this.ariaActiveDescendantElement = null;
                this.#popover.querySelector('.focus')?.classList.remove('focus');
                item.classList.remove('focus');
            });

            item.addEventListener('focus', event => {
                this.ariaActiveDescendantElement = item;
                this.#popover.querySelector('.focus')?.classList.remove('focus');
                item.classList.add('focus');
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

        this.addEventListener('keydown', event => {
            const focus = this.#popover.querySelector('.focus');
            const firstOption = this.#popover.querySelector('li');

            switch (event.key) {
                case 'Enter':
                    if (focus) {
                        focus.click();
                        event.preventDefault();
                    }
                    break;
                case 'ArrowDown':
                    if (focus && focus.nextElementSibling) {
                        focus.classList.remove('focus');
                        focus.nextElementSibling.classList.add('focus');
                        focus.nextElementSibling.scrollIntoView();
                    } else if (!focus && firstOption) {
                        firstOption.classList.add('focus');
                        firstOption.scrollIntoView();
                    }
                    break;
                case 'ArrowUp':
                    if (focus && focus.previousElementSibling) {
                        focus.classList.remove('focus');
                        focus.previousElementSibling.classList.add('focus');
                        focus.previousElementSibling.scrollIntoView();
                    }
                    break;
                // Escape: already handled by popover
                // ArrowRight: already handled by input element
                // ArrowLeft: already handled by input element
            }
        })

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
