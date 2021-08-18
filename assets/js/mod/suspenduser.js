const banTemplates = JSON.parse(document.getElementById("ban-templates").textContent);
const templateId = document.getElementById("template_id");
const suspendAction = document.getElementById("suspendaction");
const suspendDuration = document.getElementById("duration");
const suspendReason = document.getElementById("suspendreason");

function fillCustomAction() {
  if (!this.value) {
    return;
  }

  const tmpl = banTemplates[this.value];

  if (tmpl.days < 0) {
    suspendAction.selectedIndex = 2;
    suspendDuration.value = "";
  } else {
    suspendAction.selectedIndex = 1;
    suspendDuration.value = tmpl.days;
  }

  suspendReason.textContent = tmpl.reason;
}

templateId.addEventListener("change", fillCustomAction);
