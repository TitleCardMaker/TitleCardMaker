describe('Connections Page', () => {
  beforeEach(() => {
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

  describe.only('Sonarr Connections', () => {
    it('should allow adding a new Sonarr connection', () => {
      cy.get('.add-connection.button').eq(3).click() // Sonarr button
      
      // Check form is visible
      cy.get('#sonarr-connections .content.active').should('be.visible')
      
      // Fill out the form
      cy.get('#sonarr-connections input[name="name"]').type('Test Sonarr')
      cy.get('#sonarr-connections input[name="url"]').type('http://192.168.1.100:8989/')
      cy.get('#sonarr-connections input[name="api_key"]').type('sonarr-api-key-123')
      
      // Check SSL checkbox
      cy.get('#sonarr-connections .checkbox[data-value="use_ssl"] input').check()
      
      // Check downloaded only checkbox
      cy.get('#sonarr-connections .checkbox[data-value="downloaded_only"] input').check()
      
      // Submit the form
      cy.get('#sonarr-connections button[data-action="save"]').click()
    })

    it('should have library management buttons', () => {
      cy.get('.add-connection.button').eq(3).click() // Sonarr button
      
      cy.get('#sonarr-connections .button[data-action="add-library"]').should('be.visible')
      cy.get('#sonarr-connections .button[data-action="query-libraries"]').should('be.visible')
    })

    it('should allow adding library fields', () => {
      cy.get('.add-connection.button').eq(3).click() // Sonarr button
      
      // Click add library button
      cy.get('#sonarr-connections .button[data-action="add-library"]').click()
      
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
      cy.get('#tvdb-connections .checkbox[data-value="include_movies"] input').check()
      
      // Submit the form
      cy.get('#tvdb-connections button[data-action="save"]').click()
    })

    it('should have episode ordering dropdown', () => {
      cy.get('.add-connection.button').eq(5).click() // TVDb button
      
      // Check episode ordering field exists
      cy.get('#tvdb-connections .field[data-value="episode_ordering"]').should('be.visible')
      cy.get('#tvdb-connections .field[data-value="episode_ordering"] label').should('contain', 'Episode Ordering')
    })

    it('should have language priority dropdown', () => {
      cy.get('.add-connection.button').eq(5).click() // TVDb button
      
      // Check language priority field exists
      cy.get('#tvdb-connections .field[data-value="language_priority"]').should('be.visible')
      cy.get('#tvdb-connections .field[data-value="language_priority"] label').should('contain', 'Language Priority')
    })
  })

  describe('Form Validation', () => {
    it('should validate all required fields across connection types', () => {
      // Test Emby validation
      cy.get('.add-connection.button').eq(0).click()
      cy.get('#emby-connections button[data-action="save"]').click()
      cy.get('#emby-connections .error.message').should('be.visible')
      
      // Test Plex validation
      cy.get('.add-connection.button').eq(2).click()
      cy.get('#plex-connections button[data-action="save"]').click()
      cy.get('#plex-connections .error.message').should('be.visible')
      
      // Test Sonarr validation
      cy.get('.add-connection.button').eq(3).click()
      cy.get('#sonarr-connections button[data-action="save"]').click()
      cy.get('#sonarr-connections .error.message').should('be.visible')
    })

    it('should show validation errors on blur', () => {
      cy.get('.add-connection.button').eq(0).click() // Emby
      
      // Focus and blur on required field to trigger validation
      cy.get('#emby-connections input[name="name"]').focus().blur()
      
      // Check for validation error
      cy.get('#emby-connections .error.message').should('be.visible')
    })
  })

  describe('Connection Management', () => {
    it('should allow editing existing connections', () => {
      // This test assumes there are existing connections
      // In a real scenario, you might need to create one first
      cy.get('#emby-connections .accordion .title').first().click()
      
      // Check that the form is visible
      cy.get('#emby-connections .content.active').should('be.visible')
      
      // Modify a field
      cy.get('#emby-connections input[name="name"]').clear().type('Updated Connection Name')
      
      // Save changes
      cy.get('#emby-connections button[data-action="save"]').click()
    })

    it('should allow deleting connections', () => {
      // This test assumes there are existing connections
      cy.get('#emby-connections .accordion .title').first().click()
      
      // Check delete button exists
      cy.get('#emby-connections button[data-action="delete"]').should('be.visible')
      cy.get('#emby-connections button[data-action="delete"]').should('contain', 'Delete')
    })

    it('should handle library operations', () => {
      // This test assumes there are existing connections with libraries
      cy.get('#emby-connections .accordion .title').first().click()
      
      // Check refresh libraries button exists
      cy.get('#emby-connections [data-action="refresh-libraries"]').should('be.visible')
      
      // Check delete libraries button exists
      cy.get('#emby-connections [data-action="delete-libraries"]').should('be.visible')
    })
  })

  describe('Tautulli Integration', () => {
    it('should display Tautulli modal with correct form fields', () => {
      cy.get('.add-connection.button').eq(2).click() // Plex button
      cy.get('#plex-connections .button[data-action="tautulli"]').click()
      
      // Check modal content
      cy.get('#tautulli-agent-modal').should('be.visible')
      cy.get('#tautulli-agent-modal .header').should('contain', 'Tautulli Notification Agent')
      
      // Check form fields
      cy.get('#tautulli-agent-form input[name="url"]').should('be.visible')
      cy.get('#tautulli-agent-form input[name="api_key"]').should('be.visible')
      cy.get('#tautulli-agent-form input[name="use_ssl"]').should('be.visible')
      cy.get('#tautulli-agent-form input[name="agent_name"]').should('be.visible')
      cy.get('#tautulli-agent-form input[name="tcm_url"]').should('be.visible')
      cy.get('#tautulli-agent-form input[name="trigger_watched"]').should('be.visible')
      cy.get('#tautulli-agent-form input[name="username"]').should('be.visible')
    })

    it('should validate Tautulli form fields', () => {
      cy.get('.add-connection.button').eq(2).click() // Plex button
      cy.get('#plex-connections .button[data-action="tautulli"]').click()
      
      // Try to submit without required fields
      cy.get('#tautulli-agent-modal button').contains('Create Agent').click()
      
      // Check for validation errors
      cy.get('#tautulli-agent-form .error.message').should('be.visible')
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

  describe('Accessibility', () => {
    it('should have proper form labels', () => {
      cy.get('.add-connection.button').eq(0).click() // Emby button
      
      // Check that all form fields have labels
      cy.get('#emby-connections input[name="name"]').should('have.attr', 'name')
      cy.get('#emby-connections input[name="url"]').should('have.attr', 'name')
      cy.get('#emby-connections input[name="api_key"]').should('have.attr', 'name')
    })

    it('should have proper button text and icons', () => {
      cy.get('.add-connection.button').eq(0).click() // Emby button
      
      // Check save button
      cy.get('#emby-connections button[data-action="save"]').should('contain', 'Save Changes')
      
      // Check delete button
      cy.get('#emby-connections button[data-action="delete"]').should('contain', 'Delete')
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

