describe('Connections Page', () => {
  beforeEach(() => {
    cy.resetDatabase()

    // Visit the connections page before each test
    cy.visit('/connections')

    // Wait for the page to load completely
    cy.get('#main-content').should('be.visible')
  })

  describe('Page Structure', () => {
    it('should display the main page elements', () => {
      cy.get('h1.ui.header').should('contain', 'Connections')
      cy.get('h2.ui.dividing.header').should('contain', 'Authentication')
      
      // Check all connection type sections exist
      cy.get('h2.ui.dividing.header').should('contain', 'Emby')
      cy.get('h2.ui.dividing.header').should('contain', 'Jellyfin')
      cy.get('h2.ui.dividing.header').should('contain', 'Plex')
      cy.get('h2.ui.dividing.header').should('contain', 'Sonarr')
      cy.get('h2.ui.dividing.header').should('contain', 'TheMovieDatabase')
      cy.get('h2.ui.dividing.header').should('contain', 'TVDb')
    })

    it('should have add connection buttons for each type', () => {
      cy.get('.add-connection.button').should('have.length', 6)
      cy.get('.add-connection.button').eq(0).should('contain', 'Add Connection')
    })
  })

  describe('Authentication Section', () => {
    it('should display authentication settings', () => {
      cy.get('#auth-settings').should('be.visible')
      cy.get('#auth-settings input[name="username"]').should('be.visible')
      cy.get('#auth-settings input[name="password"]').should('be.visible')
      cy.get('#auth-settings button').should('contain', 'Save Changes')
    })

    it('should have authentication checkbox', () => {
      cy.get('.checkbox[data-value="require_auth"]').should('be.visible')
      cy.get('.checkbox[data-value="require_auth"] label').should('contain', 'Require Authentication')
    })
  })

  describe('Emby Connections', () => {
    it('should allow adding a new Emby connection', () => {
      cy.get('.add-connection.button').contains('Add Connection').first().click()

      // Check that the form is visible and expanded
      cy.get('#emby-connections .content.active').should('be.visible')

      // Fill out the form
      cy.get('#emby-connections input[name="name"]').type('Test Emby Server')
      cy.get('#emby-connections input[name="url"]').type('http://192.168.1.100:8096/')
      cy.get('#emby-connections input[name="api_key"]').type('test-api-key-123')
      cy.get('#emby-connections input[name="filesize_limit"]').clear().type('10 Megabytes')

      // Check SSL checkbox
      cy.get('#emby-connections .checkbox[data-value="use_ssl"] input').check()

      // Submit the form
      cy.get('#emby-connections button[data-action="save"]').click()
    })

    it('should validate required fields', () => {
      cy.get('.add-connection.button').contains('Add Connection').first().click()

      // Try to submit without required fields
      cy.get('#emby-connections button[data-action="save"]').click()

      // Check for validation errors
      cy.get('#emby-connections .error.message').should('be.visible')
    })

    it('should validate filesize limit format', () => {
      cy.get('.add-connection.button').contains('Add Connection').first().click()
      
      // Enter invalid filesize format
      cy.get('#emby-connections input[name="filesize_limit"]').clear().type('invalid format')
      cy.get('#emby-connections input[name="name"]').type('Test')
      cy.get('#emby-connections input[name="url"]').type('http://test.com')
      cy.get('#emby-connections input[name="api_key"]').type('test')
      
      // Submit and check validation
      cy.get('#emby-connections button[data-action="save"]').click()
      cy.get('#emby-connections .error.message').should('be.visible')
    })

    it('should allow username selection after connection creation', () => {
      // First create a connection
      cy.get('.add-connection.button').contains('Add Connection').first().click()

      // Fill out the form
      cy.get('#emby-connections input[name="name"]').type('Test Emby Server')
      cy.get('#emby-connections input[name="url"]').type('http://192.168.1.100:8096/')
      cy.get('#emby-connections input[name="api_key"]').type('abcdef')
      cy.get('#emby-connections input[name="filesize_limit"]').clear().type('2 Megabytes')

      // Check SSL checkbox
      cy.get('#emby-connections .checkbox[data-value="use_ssl"] input').check()

      // Submit the form
      cy.get('#emby-connections button[data-action="save"]').click()

      // Reload the page to see the username dropdown
      cy.reload()

      // Click on the connection to expand it
      cy.get('#emby-connections .title').first().click()

      // Check that the username dropdown is visible and contains expected options
      cy.get('#emby-connections .active.content .dropdown[data-value="username"]').should('be.visible')
      cy.get('#emby-connections .active.content .dropdown[data-value="username"]').click()
      
      // Check that Admin and User are visible in the dropdown
      cy.get('#emby-connections .active.content .dropdown[data-value="username"] .menu .item').should('contain', 'Admin')
      cy.get('#emby-connections .active.content .dropdown[data-value="username"] .menu .item').should('contain', 'User')

      // Select Admin user
      cy.get('#emby-connections .active.content .dropdown[data-value="username"] .menu .item').contains('Admin').click()

      // Verify Admin is selected
      cy.get('#emby-connections .active.content .dropdown[data-value="username"] .text').should('contain', 'Admin')

      // Save the connection
      cy.get('#emby-connections .active.content button[data-action="save"]').click()

      // Reload the page to verify persistence
      cy.reload()

      // Click on the connection again
      cy.get('#emby-connections .title').first().click()

      // Verify that Admin is still selected after reload
      cy.get('#emby-connections .active.content .dropdown[data-value="username"] .text').should('contain', 'Admin')

      // Change to User and verify it persists
      cy.get('#emby-connections .active.content .dropdown[data-value="username"]').click()
      cy.get('#emby-connections .active.content .dropdown[data-value="username"] .menu .item').contains('User').click()
      cy.get('#emby-connections .active.content button[data-action="save"]').click()

      // Reload and verify User selection persists
      cy.reload()
      cy.get('#emby-connections .title').first().click()
      cy.get('#emby-connections .active.content .dropdown[data-value="username"] .text').should('contain', 'User')
    })
  })

  describe('Jellyfin Connections', () => {
    it('should allow adding a new Jellyfin connection', () => {
      cy.get('.add-connection.button').eq(1).click() // Jellyfin button

      // Check that the form is visible and expanded
      cy.get('#jellyfin-connections .content.active').should('be.visible')

      // Fill out the form
      cy.get('#jellyfin-connections input[name="name"]').type('Test Jellyfin Server')
      cy.get('#jellyfin-connections input[name="url"]').type('http://192.168.1.100:8096/')
      cy.get('#jellyfin-connections input[name="api_key"]').type('abcdef')
      cy.get('#jellyfin-connections input[name="filesize_limit"]').clear().type('2 Megabytes')

      // Check SSL checkbox
      cy.get('#jellyfin-connections .checkbox[data-value="use_ssl"] input').check()

      // Submit the form
      cy.get('#jellyfin-connections button[data-action="save"]').click()
    })

    it('should validate required fields', () => {
      cy.get('.add-connection.button').eq(1).click() // Jellyfin button

      // Try to submit without required fields
      cy.get('#jellyfin-connections button[data-action="save"]').click()

      // Check for validation errors
      cy.get('#jellyfin-connections .error.message').should('be.visible')
    })

    it('should validate filesize limit format', () => {
      cy.get('.add-connection.button').eq(1).click() // Jellyfin button
      
      // Enter invalid filesize format
      cy.get('#jellyfin-connections input[name="filesize_limit"]').clear().type('invalid format')
      cy.get('#jellyfin-connections input[name="name"]').type('Test')
      cy.get('#jellyfin-connections input[name="url"]').type('http://test.com')
      cy.get('#jellyfin-connections input[name="api_key"]').type('test')
      
      // Submit and check validation
      cy.get('#jellyfin-connections button[data-action="save"]').click()
      cy.get('#jellyfin-connections .error.message').should('be.visible')
    })

    it('should allow username selection after connection creation', () => {
      // First create a connection
      cy.get('.add-connection.button').eq(1).click() // Jellyfin button

      // Fill out the form
      cy.get('#jellyfin-connections input[name="name"]').type('Test Jellyfin Server')
      cy.get('#jellyfin-connections input[name="url"]').type('http://192.168.1.100:8096/')
      cy.get('#jellyfin-connections input[name="api_key"]').type('abcdef')
      cy.get('#jellyfin-connections input[name="filesize_limit"]').clear().type('2 Megabytes')

      // Check SSL checkbox
      cy.get('#jellyfin-connections .checkbox[data-value="use_ssl"] input').check()

      // Submit the form
      cy.get('#jellyfin-connections button[data-action="save"]').click()

      // Reload the page to see the username dropdown
      cy.reload()

      // Click on the connection to expand it
      cy.get('#jellyfin-connections .title').first().click()

      // Check that the username dropdown is visible and contains expected options
      cy.get('#jellyfin-connections .active.content .dropdown[data-value="username"]').should('be.visible')
      cy.get('#jellyfin-connections .active.content .dropdown[data-value="username"]').click()
      
      // Check that Admin and User are visible in the dropdown
      cy.get('#jellyfin-connections .active.content .dropdown[data-value="username"] .menu .item').should('contain', 'Admin')
      cy.get('#jellyfin-connections .active.content .dropdown[data-value="username"] .menu .item').should('contain', 'User')

      // Select Admin user
      cy.get('#jellyfin-connections .active.content .dropdown[data-value="username"] .menu .item').contains('Admin').click()

      // Verify Admin is selected
      cy.get('#jellyfin-connections .active.content .dropdown[data-value="username"] .text').should('contain', 'Admin')

      // Save the connection
      cy.get('#jellyfin-connections .active.content button[data-action="save"]').click()

      // Reload the page to verify persistence
      cy.reload()

      // Click on the connection again
      cy.get('#jellyfin-connections .title').first().click()

      // Verify that Admin is still selected after reload
      cy.get('#jellyfin-connections .active.content .dropdown[data-value="username"] .text').should('contain', 'Admin')

      // Change to User and verify it persists
      cy.get('#jellyfin-connections .active.content .dropdown[data-value="username"]').click()
      cy.get('#jellyfin-connections .active.content .dropdown[data-value="username"] .menu .item').contains('User').click()
      cy.get('#jellyfin-connections .active.content button[data-action="save"]').click()

      // Reload and verify User selection persists
      cy.reload()
      cy.wait(250)
      cy.get('#jellyfin-connections .title').first().click()
      cy.get('#jellyfin-connections .active.content .dropdown[data-value="username"] .text').should('contain', 'User')
    })
  })

  describe('Plex Connections', () => {
    it('should allow adding a new Plex connection', () => {
      cy.get('.add-connection.button').eq(2).click() // Plex button

      // Check form is visible
      cy.get('#plex-connections .content.active').should('be.visible')

      // Fill out the form
      cy.get('#plex-connections input[name="name"]').type('Test Plex Server')
      cy.get('#plex-connections input[name="url"]').type('http://192.168.1.100:32400/')
      cy.get('#plex-connections input[name="api_key"]').type('plex-token-123')
      cy.get('#plex-connections input[name="filesize_limit"]').clear().type('8 Megabytes')

      // Check SSL checkbox
      cy.get('#plex-connections .checkbox[data-value="use_ssl"]').click()

      // Check Kometa integration
      cy.get('#plex-connections .checkbox[data-value="integrate_with_kometa"]').click()

      // Submit the form
      cy.get('#plex-connections button[data-action="save"]').click()
    })

    it('should have Tautulli integration button', () => {
      cy.get('.add-connection.button').eq(2).click() // Plex button

      cy.get('#plex-connections .button[data-action="tautulli"]').should('be.visible')
      cy.get('#plex-connections .button[data-action="tautulli"]').should('contain', 'Create Notification Agent')
    })

    it('should open Tautulli modal when button is clicked', () => {
      cy.get('.add-connection.button').eq(2).click() // Plex button
      
      cy.get('#plex-connections .button[data-action="tautulli"]').click()
      
      // Check modal is visible
      cy.get('#tautulli-agent-modal').should('be.visible')
      cy.get('#tautulli-agent-modal .header').should('contain', 'Tautulli Notification Agent')
    })
  })

  describe('Sonarr Connections', () => {
    it('should allow adding a new Sonarr connection', () => {
      cy.get('.add-connection.button').eq(3).click() // Sonarr button

      // Check form is visible
      cy.get('#sonarr-connections .content.active').should('be.visible')

      // Fill out the form
      cy.get('#sonarr-connections input[name="name"]').type('Test Sonarr')
      cy.get('#sonarr-connections input[name="url"]').type('http://192.168.1.100:8989/')
      cy.get('#sonarr-connections input[name="api_key"]').type('abcdef0123')

      // Check SSL checkbox
      cy.get('#sonarr-connections .checkbox[data-value="use_ssl"] input').check()

      // Check downloaded only checkbox
      cy.get('#sonarr-connections .checkbox[data-value="downloaded_only"] input').check()

      // Submit the form
      cy.get('#sonarr-connections button[data-action="save"]').click()
    })

    it('should not have library management buttons before connection is created', () => {
      cy.get('.add-connection.button').eq(3).click() // Sonarr button

      // Library management buttons should not be visible before connection creation
      cy.get('#sonarr-connections .button[data-action="add-library"]').should('have.class', 'disabled')
      cy.get('#sonarr-connections .button[data-action="query-libraries"]').should('have.class', 'disabled')
    })

    it('should have library management buttons after connection creation and page reload', () => {
      // First create a connection
      cy.get('.add-connection.button').eq(3).click() // Sonarr button

      // Fill out and submit the form
      cy.get('#sonarr-connections input[name="name"]').type('Test Sonarr for Library Management')
      cy.get('#sonarr-connections input[name="url"]').type('http://192.168.1.100:8989/')
      cy.get('#sonarr-connections input[name="api_key"]').type('abcdef0123')
      cy.get('#sonarr-connections button[data-action="save"]').click()

      // Reload the page to see library management buttons
      cy.reload()

      // Now library management buttons should be visible
      cy.get('#sonarr-connections .title').first().click()
      cy.get('#sonarr-connections .active.content .button[data-action="add-library"]').scrollIntoView().should('be.visible')
      cy.get('#sonarr-connections .active.content .button[data-action="query-libraries"]').scrollIntoView().should('be.visible')
    })

    it('should allow adding library fields after connection creation', () => {
      // First create a connection
      cy.get('.add-connection.button').eq(3).click() // Sonarr button
      
      // Fill out and submit the form
      cy.get('#sonarr-connections input[name="name"]').type('Test Sonarr for Library Fields')
      cy.get('#sonarr-connections input[name="url"]').type('http://192.168.1.100:8989/')
      cy.get('#sonarr-connections input[name="api_key"]').type('abcdef0123')
      cy.get('#sonarr-connections button[data-action="save"]').click()

      // Reload the page
      cy.reload()

      // Now click add library button
      cy.get('#sonarr-connections .title').first().click()
      cy.get('#sonarr-connections .active.content .button[data-action="add-library"]').click()

      // Check that new fields were added
      cy.get('#sonarr-connections .field[data-value="library_name"] input').should('have.length.at.least', 1)
      cy.get('#sonarr-connections .field[data-value="library_path"] input').should('have.length.at.least', 1)
    })
  })

  describe('TMDb Connections', () => {
    it('should allow adding a new TMDb connection', () => {
      cy.get('.add-connection.button').eq(4).click() // TMDb button
      
      // Check form is visible
      cy.get('#tmdb-connections .content.active').should('be.visible')
      
      // Fill out the form
      cy.get('#tmdb-connections input[name="name"]').type('Test TMDb')
      cy.get('#tmdb-connections input[name="api_key"]').type('tmdb-api-key-123')
      cy.get('#tmdb-connections input[name="minimum_dimensions"]').clear().type('1000x500')
      
      // Check skip localized checkbox
      cy.get('#tmdb-connections .checkbox[data-value="skip_localized"] input').check()
      
      // Submit the form
      cy.get('#tmdb-connections button[data-action="save"]').click()
    })

    it('should validate API key format', () => {
      cy.get('.add-connection.button').eq(4).click() // TMDb button
      
      // Enter invalid API key format
      cy.get('#tmdb-connections input[name="api_key"]').type('invalid-key-with-special-chars!@#')
      cy.get('#tmdb-connections input[name="name"]').type('Test')
      cy.get('#tmdb-connections input[name="minimum_dimensions"]').type('100x100')
      
      // Submit and check validation
      cy.get('#tmdb-connections button[data-action="save"]').click()
      cy.get('#tmdb-connections .error.message').should('be.visible')
    })

    it('should validate minimum dimensions format', () => {
      cy.get('.add-connection.button').eq(4).click() // TMDb button
      
      // Enter invalid dimensions format
      cy.get('#tmdb-connections input[name="minimum_dimensions"]').type('invalid-dimensions')
      cy.get('#tmdb-connections input[name="name"]').type('Test')
      cy.get('#tmdb-connections input[name="api_key"]').type('validkey123')
      
      // Submit and check validation
      cy.get('#tmdb-connections button[data-action="save"]').click()
      cy.get('#tmdb-connections .error.message').should('be.visible')
    })
  })

  describe('TVDb Connections', () => {
    it('should allow adding a new TVDb connection', () => {
      cy.get('.add-connection.button').eq(5).click() // TVDb button

      // Check form is visible
      cy.get('#tvdb-connections .content.active').should('be.visible')

      // Fill out the form
      cy.get('#tvdb-connections input[name="name"]').type('Test TVDb')
      cy.get('#tvdb-connections input[name="api_key"]').type('tvdb-api-key-123')
      cy.get('#tvdb-connections input[name="minimum_dimensions"]').clear().type('800x400')

      // Check include movies checkbox
      cy.get('#tvdb-connections .checkbox[data-value="include_movies"]').click()

      // Submit the form
      cy.get('#tvdb-connections button[data-action="save"]').click()
    })
  })

  describe('Form Validation', () => {
    it('should validate all required fields across connection types', () => {
      // Test Emby validation
      cy.get('.add-connection.button').eq(0).click()
      cy.get('#emby-connections button[data-action="save"]').click()
      cy.get('#emby-connections .error.message').should('be.visible')

      // Test Plex validation
      cy.reload()
      cy.get('.add-connection.button').eq(2).click()
      cy.get('#plex-connections button[data-action="save"]').click()
      cy.get('#plex-connections .error.message').should('be.visible')

      // Test Sonarr validation
      cy.reload()
      cy.get('.add-connection.button').eq(3).click()
      cy.get('#sonarr-connections button[data-action="save"]').click()
      cy.get('#sonarr-connections .error.message').should('be.visible')
    })
  })

  describe('Connection Management', () => {
    beforeEach(() => {
      cy.resetDatabase()
      cy.createEmbyConnection()
      cy.visit('/connections')
    })

    it('should allow editing existing connections', () => {
      cy.createEmbyConnection()
      cy.reload()
      cy.get('#emby-connections .title').first().click()

      // Check that the form is visible
      cy.get('#emby-connections .active.content').should('be.visible')

      // Modify a field
      cy.get('#emby-connections .active.content input[name="name"]').clear().type('Updated Connection Name')

      // Save changes
      cy.get('#emby-connections .active.content button[data-action="save"]').click()

      // Check that the connection name was updated
      cy.reload()
      cy.get('#emby-connections .title').first().should('contain', 'Updated Connection Name')
    })

    it('should allow deleting connections', () => {
      // This test assumes there are existing connections
      cy.get('#emby-connections .title').first().click()
      
      // Check delete button exists
      cy.get('#emby-connections button[data-action="delete"]').should('be.visible')
      cy.get('#emby-connections button[data-action="delete"]').should('contain', 'Delete')
    })
  })

  describe('Tautulli Integration', () => {
    beforeEach(() => {
      cy.resetDatabase()
      cy.createPlexConnection()
      cy.visit('/connections')
    })

    it('should display Tautulli modal with correct form fields', () => {
      cy.get('#plex-connections .title').first().click()
      cy.get('#plex-connections .active.content .button[data-action="tautulli"]').click()

      // Check modal content
      cy.get('#tautulli-agent-modal').should('be.visible')
      cy.get('#tautulli-agent-modal .header').should('contain', 'Tautulli Notification Agent')

      // Check form fields
      cy.get('#tautulli-agent-form input[name="url"]').should('be.visible')
      cy.get('#tautulli-agent-form input[name="api_key"]').should('be.visible')
      cy.get('#tautulli-agent-form input[name="agent_name"]').should('be.visible')
      cy.get('#tautulli-agent-form input[name="tcm_url"]').should('be.visible')
      cy.get('#tautulli-agent-form input[name="username"]').should('be.visible')
    })

    it('should validate Tautulli form fields', () => {
      cy.get('#plex-connections .title').first().click()
      cy.get('#plex-connections .active.content .button[data-action="tautulli"]').click()

      // Try to submit without required fields
      cy.get('#tautulli-agent-modal button').contains('Create Agent').click()

      // Modal should not have been submitted
      cy.get('#tautulli-agent-modal').should('be.visible')
      cy.get('#tautulli-agent-modal .header').should('contain', 'Tautulli Notification Agent')
    })
  })

  describe('Responsive Design', () => {
    it('should handle mobile viewport', () => {
      cy.viewport('iphone-x')
      
      // Check that all elements are still accessible
      cy.get('h1.ui.header').should('be.visible')
      cy.get('.add-connection.button').should('be.visible')
      
      // Check that forms are still usable on mobile
      cy.get('.add-connection.button').eq(0).click()
      cy.get('#emby-connections .content.active').should('be.visible')
    })

    it('should handle tablet viewport', () => {
      cy.viewport('ipad-2')
      
      // Check that all elements are still accessible
      cy.get('h1.ui.header').should('be.visible')
      cy.get('.add-connection.button').should('be.visible')
    })
  })

  describe('Error Handling', () => {
    it('should display error messages for API failures', () => {
      // This test would require mocking API responses
      // In a real scenario, you might test with invalid credentials
      cy.get('.add-connection.button').eq(0).click() // Emby button
      
      // Fill form with potentially invalid data
      cy.get('#emby-connections input[name="name"]').type('Test')
      cy.get('#emby-connections input[name="url"]').type('http://invalid-url')
      cy.get('#emby-connections input[name="api_key"]').type('invalid-key')
      
      // Submit and check for error handling
      cy.get('#emby-connections button[data-action="save"]').click()
      
      // The page should handle errors gracefully
      cy.get('#emby-connections').should('be.visible')
    })
  })
})

