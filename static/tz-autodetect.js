var tz_button = document.getElementById('tz-autodetect');
var tz_dropdown = document.getElementById('timezone');
tz_button.style.display = 'inline-block';
tz_button.onclick = function () {
    var timezone = jstz.determine();
    tz_dropdown.value = timezone.name();
}
