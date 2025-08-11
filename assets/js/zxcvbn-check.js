import {forEach} from './util/array-like.js';

const strengthMessages = [
    "Crackable password",
    "Over easy password",
    "Yolkay password",
    "Eggscelent password",
    "Eggsemplary password!",
];

const init = () => {
    const passwordStrengthIndicators = document.getElementsByClassName("password-strength");

    forEach(passwordStrengthIndicators, passwordStrength => {
        const passwordField = document.getElementById(passwordStrength.getAttribute("data-password-input"));
        const personalFields =
            (passwordStrength.getAttribute("data-personal-inputs") || "")
                .split(",")
                .filter(Boolean)
                .map(document.getElementById, document);
        const personalData =
            (passwordStrength.getAttribute("data-personal-data") || "")
                .match(/[a-zA-Z0-9]+/g) || [];

        const check = () => {
            if (!passwordField.value) {
                passwordStrength.className = "password-strength password-strength-empty";
                passwordStrength.textContent = "";
                return;
            }

            const personalStrings =
                personalFields
                    .reduce((strings, field) => {
                        const value = field.value;
                        const word = /[a-zA-Z0-9]+/g;

                        for (let match; (match = word.exec(value));) {
                            strings.push(match[0]);
                        }

                        return strings;
                    }, [])
                    .concat(personalData);

            const result = zxcvbn(passwordField.value, personalStrings);

            passwordStrength.className = "password-strength password-strength-" + result.score;
            passwordStrength.textContent = strengthMessages[result.score];
        };

        passwordField.addEventListener("input", check);

        personalFields.forEach(personalField => {
            if (personalField.nodeName === "SELECT") {
                personalField.addEventListener("change", check);
            } else {
                personalField.addEventListener("input", check);
            }
        });

        check();
    });
};

if (window.zxcvbn) {
    init();
} else {
    window.zxcvbn_load_hook = init;
}
