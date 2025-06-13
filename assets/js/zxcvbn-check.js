(function () {
    "use strict";

    var strengthMessages = [
        "Crackable password",
        "Over easy password",
        "Yolkay password",
        "Eggscelent password",
        "Eggsemplary password!",
    ];

    function forEach(list, callback) {
        for (var i = 0, l = list.length; i < l; i++) {
            callback(list[i]);
        }
    }

    function init() {
        var passwordStrengthIndicators = document.getElementsByClassName("password-strength");

        forEach(passwordStrengthIndicators, function (passwordStrength) {
            var passwordField = document.getElementById(passwordStrength.getAttribute("data-password-input"));
            var personalFields =
                (passwordStrength.getAttribute("data-personal-inputs") || "")
                    .split(",")
                    .filter(Boolean)
                    .map(document.getElementById, document);
            var personalData =
                (passwordStrength.getAttribute("data-personal-data") || "")
                    .match(/[a-zA-Z0-9]+/g) || [];

            function check() {
                if (!passwordField.value) {
                    passwordStrength.className = "password-strength password-strength-empty";
                    passwordStrength.textContent = "";
                    return;
                }

                var personalStrings =
                    personalFields
                        .reduce(function (strings, field) {
                            var value = field.value;
                            var word = /[a-zA-Z0-9]+/g;
                            var match;

                            while ((match = word.exec(value))) {
                                strings.push(match[0]);
                            }

                            return strings;
                        }, [])
                        .concat(personalData);

                var result = zxcvbn(passwordField.value, personalStrings);

                passwordStrength.className = "password-strength password-strength-" + result.score;
                passwordStrength.textContent = strengthMessages[result.score];
            }

            passwordField.addEventListener("input", check);

            personalFields.forEach(function (personalField) {
                if (personalField.nodeName === "SELECT") {
                    personalField.addEventListener("change", check);
                } else {
                    personalField.addEventListener("input", check);
                }
            });

            check();
        });
    }

    if (window.zxcvbn) {
        init();
    } else {
        window.zxcvbn_load_hook = init;
    }
})();
