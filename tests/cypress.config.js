const { defineConfig } = require('cypress')

module.exports = defineConfig({
  projectId: "sod537",
  reporter: 'mochawesome',
  numTestsKeptInMemory: 5,
  viewportHeight: 1080,
  viewportWidth: 1920,
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
        'cypress/e2e/sync.cy.js',
        'cypress/e2e/add.cy.js',
      ]
      return config
    },
  },
});
