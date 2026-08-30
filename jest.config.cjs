// Jest configuration for the Weasyl front-end TypeScript code
/**
 * This uses the "flat" config format (jest.config.cjs) compatible with
 * Jest v30. It presets ts-jest for TypeScript support and uses the jsdom
 * environment so that DOM APIs (document, window, etc.) are available in
 * the tests.
 */
module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  // Look for test files under the assets/js directory
  testMatch: ["<rootDir>/assets/js/**/*.test.ts"],
  // Transform TypeScript files via ts-jest
  transform: {
    "^.+\\.tsx?$": "ts-jest",
  },
  moduleNameMapper: {
    "^(\\.{1,2}/.*)\\.js$": "$1",
  },
  // Optional: hide verbose Jest output
  verbose: true,
};
