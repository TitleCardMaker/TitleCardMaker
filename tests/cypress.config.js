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
        'cypress/e2e/add.cy.js',
        'cypress/e2e/connections.cy.js',
        'cypress/e2e/fonts.cy.js',
        'cypress/e2e/logs.cy.js',
        'cypress/e2e/navigation.cy.js',
        'cypress/e2e/scheduler.cy.js',
        'cypress/e2e/settings.cy.js',
        'cypress/e2e/sync.cy.js',
        'cypress/e2e/templates.cy.js',
      ]

      // Force Chrome to open exactly at the viewport size
      on('before:browser:launch', (browser = {}, launchOptions) => {
        const vw = config.viewportWidth
        const vh = config.viewportHeight

        if (browser.name === 'electron') {
          launchOptions.preferences = {
            ...(launchOptions.preferences || {}),
            width: vw,
            height: vh,
          }
        }

        if (['chrome', 'chromium', 'edge'].includes(browser.name)) {
          launchOptions.args ??= []
          if (
            browser.isHeadless &&
            !launchOptions.args.some((arg) =>
              String(arg).startsWith('--window-size='),
            )
          ) {
            launchOptions.args.push(`--window-size=${vw},${vh}`)
          }
          if (!launchOptions.args.includes('--force-device-scale-factor=1')) {
            launchOptions.args.push('--force-device-scale-factor=1')
          }
        }

        return launchOptions
      })

      return config
    },
  },
});
