class LocalTime extends HTMLElement {
    #dateText;
    #timeText;
    #slot;

    constructor() {
        super();

        const slot = document.createElement('slot');
        this.#slot = slot;

        slot.onslotchange = () => {
            this.#update();
        };

        this.attachShadow({mode: 'open'}).append(slot);
    }

    static get observedAttributes() {
        return ['data-timestamp'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        const timestamp = parseInt(this.getAttribute('data-timestamp'), 10);
        const d = new Date(timestamp * 1000);

        this.#dateText = d.toLocaleString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hourCycle: 'h23',
        });

        this.#timeText = d.toLocaleString('en-US', {
            hour: 'numeric',
            minute: 'numeric',
            second: 'numeric',
            hourCycle: 'h23',
            timeZoneName: 'short',
        });

        this.#update();
    }

    #update() {
        if (this.#dateText === undefined) {
            return;
        }

        for (const element of this.#slot.assignedElements()) {
            if (element.classList.contains('local-time-date')) {
                element.textContent = this.#dateText;
            } else if (element.classList.contains('local-time-time')) {
                element.textContent = this.#timeText;
            }
        }
    }
}

const defineLocalTime = () => {
    customElements.define('local-time', LocalTime);
};

export default defineLocalTime;
