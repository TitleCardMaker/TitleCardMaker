// ***********************************************************
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

import './commands'

// Avoid scaling the app to fit the runner when capturing (failure screenshots
// otherwise look "zoomed" vs the real viewport).
Cypress.Screenshot.defaults({
  scale: false,
})

// Before all test suites, reset the database and global options
before(() => {
  cy.resetDatabase();
});
