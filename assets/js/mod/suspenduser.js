import BAN_TEMPLATES from './ban-templates.json' with {type: 'json'};

const templateId = document.getElementById('template_id');
const suspendAction = document.getElementById('suspendaction');
const suspendDuration = document.getElementById('duration');
const suspendReason = document.getElementById('suspendreason');

for (const [key, {name}] of Object.entries(BAN_TEMPLATES)) {
    templateId.options.add(new Option(name, key));
}

function fillCustomAction() {
    if (!this.value) {
        return;
    }

    const tmpl = BAN_TEMPLATES[this.value];

    if (tmpl.days < 0) {
        suspendAction.selectedIndex = 2;
        suspendDuration.value = '';
    } else {
        suspendAction.selectedIndex = 1;
        suspendDuration.value = tmpl.days;
    }

    suspendReason.defaultValue = tmpl.reason;
}

templateId.addEventListener('change', fillCustomAction);
templateId.disabled = false;
