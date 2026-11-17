class DateGroupHeader extends HTMLDivElement {
    static get observedAttributes() {
        return ['data-compare'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        const [previous, current] = newValue.split(',').map(p => new Date(p * 1000));

        this.hidden =
            previous.getFullYear() === current.getFullYear()
            && previous.getMonth() === current.getMonth()
            && previous.getDate() === current.getDate();
    }
}

const defineDateGroupHeader = () => {
    customElements.define('date-group-header', DateGroupHeader, {extends: 'div'});
};

export default defineDateGroupHeader;
