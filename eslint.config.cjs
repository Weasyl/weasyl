const eslintJs = require("@eslint/js");
const globals = {
  // Browser globals
  window: "readonly", document: "readonly", navigator: "readonly",
  location: "readonly", customElements: "readonly", Option: "readonly",
  fetch: "readonly", URLSearchParams: "readonly", AbortController: "readonly",
  FormData: "readonly", localStorage: "readonly", setTimeout: "readonly",
  clearTimeout: "readonly", console: "readonly", Event: "readonly",
  // Project specifics
  $: "readonly", jQuery: "readonly", zxcvbn: "readonly",
  RufflePlayer: "readonly", RUFFLE_SRC: "readonly", MARKED_SRC: "readonly",
  // Node / Build scripts
  __dirname: "readonly", process: "readonly", require: "readonly",
  module: "readonly",
  // Jest globals
  describe: "readonly", test: "readonly", it: "readonly", expect: "readonly",
  beforeEach: "readonly", afterEach: "readonly", beforeAll: "readonly", afterAll: "readonly"
};

module.exports = [
  eslintJs.configs.recommended,
  {
    ignores: [
      "dist/**", 
      "node_modules/**", 
      "assets/js/jquery-*.js",
      "assets/js/jquery.*.js"
    ]
  },
  {
    files: ["**/*.ts", "**/*.tsx", "**/*.js"],
    languageOptions: {
      parser: require("@typescript-eslint/parser"),
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: "module",
      },
      globals
    },
    plugins: {
      "@typescript-eslint": require("@typescript-eslint/eslint-plugin")
    },
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "off"
    }
  }
];
