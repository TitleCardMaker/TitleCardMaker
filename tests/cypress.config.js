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

      // Keep the *browser window* at least as large as the configured viewport.
      // - Default Electron often ignores preferences alone; pass Chromium switches via args.
      // - Only applying --window-size for headless Chrome breaks CI when DISPLAY/Xvfb runs
      //   headed, so window-size is applied whenever it is not already set.
      on('before:browser:launch', (browser = {}, launchOptions) => {
        const vw = config.viewportWidth
        const vh = config.viewportHeight

        const ensureArg = (args, flag, value = null) => {
          const prefix = value == null ? flag : `${flag}=`
          if (args.some((a) => String(a).startsWith(prefix))) return
          args.push(value == null ? flag : `${flag}=${value}`)
        }

        if (browser.name === 'electron') {
          launchOptions.args ??= []
          ensureArg(launchOptions.args, '--window-size', `${vw},${vh}`)
          ensureArg(launchOptions.args, '--force-device-scale-factor', '1')
          launchOptions.preferences = {
            ...(launchOptions.preferences || {}),
            width: vw,
            height: vh,
          }
        }

        if (['chrome', 'chromium', 'edge'].includes(browser.name)) {
          launchOptions.args ??= []
          ensureArg(launchOptions.args, '--window-size', `${vw},${vh}`)
          ensureArg(launchOptions.args, '--force-device-scale-factor', '1')
        }

        return launchOptions
      })

      return config
    },
  },
});
