const { defineConfig } = require('cypress')

module.exports = defineConfig({
  projectId: "sod537",
  reporter: 'mochawesome',
  numTestsKeptInMemory: 5,
  reporterOptions: {
    reportDir: 'cypress/results',
    charts: true,
    overwrite: false,
    html: false,
    json: true,
  },
  e2e: {
    baseUrl: 'http://localhost:4242',
    setupNodeEvents(on, config) {
      config.specPattern = [
        'cypress/e2e/navigation.cy.js',
        'cypress/e2e/scheduler.cy.js',
        'cypress/e2e/settings.cy.js',
        'cypress/e2e/templates.cy.js',
      ]
      return config
    },
  },
});
