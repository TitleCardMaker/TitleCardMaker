describe('Sync Page', () => {
  beforeEach(() => {
    // Reset database to ensure clean state
    cy.resetDatabase();
    
    // Visit the sync page
    cy.visit('/sync');
  });

  describe('Page Structure and Navigation', () => {
    it('displays the sync page with correct title', () => {
      cy.get('h1.ui.header').should('contain', 'Syncs');
      cy.url().should('contain', '/sync');
    });

    it('shows all connection sections', () => {
      cy.createEmbyConnection(true);
      cy.createJellyfinConnection(true);
      cy.createPlexConnection(true);
      cy.createSonarrConnection(true);
      cy.reload();

      ['emby', 'jellyfin', 'plex', 'sonarr'].forEach(connection => {
        cy.get(`section[data-connection="${connection}"]`).should('exist');
        cy.get(`section[data-connection="${connection}"] h3`).should('contain', connection.charAt(0).toUpperCase() + connection.slice(1));
      });
    });

    it('shows warning when no connections are configured', () => {
      cy.get('.ui.warning.floating.message').should('exist');
      cy.get('.ui.warning.floating.message').should('contain', 'Please add an Emby, Jellyfin, Plex, or Sonarr Connection');
      cy.get('.ui.warning.floating.message a[href="/connections"]').should('exist');
    });

    it('shows next sync section when connections are available', () => {
      // Create a connection first
      cy.createEmbyConnection(true).then(() => {
        cy.visit('/sync');
        cy.get('#next-sync').should('exist');
      });
    });
  });

  describe('Add Sync Modals', () => {
    beforeEach(() => {
      cy.createEmbyConnection(true);
      cy.createJellyfinConnection(true);
      cy.createPlexConnection(true);
      cy.createSonarrConnection(true);

      cy.visit('/sync');
    });

    it('opens Emby sync modal when clicking add button', () => {
      cy.get('#add-emby-sync').click();
      cy.get('#add-emby-sync-modal').should('be.visible');
      cy.get('#add-emby-sync-modal .header').should('contain', 'New Emby Sync');
    });

    it('opens Jellyfin sync modal when clicking add button', () => {
      cy.get('#add-jellyfin-sync').click();
      cy.get('#add-jellyfin-sync-modal').should('be.visible');
      cy.get('#add-jellyfin-sync-modal .header').should('contain', 'New Jellyfin Sync');
    });

    it('opens Plex sync modal when clicking add button', () => {
      cy.get('#add-plex-sync').click();
      cy.get('#add-plex-sync-modal').should('be.visible');
      cy.get('#add-plex-sync-modal .header').should('contain', 'New Plex Sync');
    });

    it('opens Sonarr sync modal when clicking add button', () => {
      cy.get('#add-sonarr-sync').click();
      cy.get('#add-sonarr-sync-modal').should('be.visible');
      cy.get('#add-sonarr-sync-modal .header').should('contain', 'New Sonarr Sync');
    });

    it('closes modal when clicking close icon', () => {
      cy.get('#add-emby-sync').click();
      cy.get('#add-emby-sync-modal').should('be.visible');
      cy.get('#add-emby-sync-modal .close.icon').click();
      cy.get('#add-emby-sync-modal').should('not.be.visible');
    });
  });

  describe('Emby Sync Form', () => {
    beforeEach(() => {
      cy.createEmbyConnection(true);
      cy.visit('/sync');
      cy.get('#add-emby-sync').click();
    });

    it('displays all required form fields', () => {
      cy.get('#emby-sync-form').within(() => {
        cy.get('input[name="interface_id"]').should('exist');
        cy.get('input[name="name"]').should('exist');
        cy.get('input[name="template_ids"]').should('exist');
        cy.get('input[name="add_as_unmonitored"]').should('exist');
        cy.get('input[name="required_tags"]').should('exist');
        cy.get('input[name="required_libraries"]').should('exist');
        cy.get('input[name="excluded_tags"]').should('exist');
        cy.get('input[name="excluded_libraries"]').should('exist');
      });
    });

    it('populates connection dropdown with available connections', () => {
      cy.get('#add-emby-sync-modal [data-type="emby_connections"]').click();
      cy.get('#add-emby-sync-modal [data-type="emby_connections"] .menu .item').should('contain', 'Emby');
    });

    it('requires connection selection', () => {
      cy.get('#add-emby-sync-modal').within(() => {
        cy.get('input[name="name"]').type('Test Sync');
        cy.get('button').scrollIntoView().click();
      });
      
      // Form should not submit without connection
      cy.get('#add-emby-sync-modal').should('be.visible');
    });

    it('requires sync name', () => {
      cy.get('#add-emby-sync-modal [data-type="emby_connections"]').click();
      cy.get('#add-emby-sync-modal [data-type="emby_connections"] .menu .item').contains('Emby').click();
      
      cy.get('#add-emby-sync-modal button').click();
      
      // Form should not submit without name
      cy.get('#add-emby-sync-modal').should('be.visible');
    });

    it('submits form successfully with valid data', () => {
      // Select connection
      cy.selectDropdown('#add-emby-sync-modal', '.dropdown[data-value="interface_id"]', 'Emby');

      // Fill required fields
      cy.get('#emby-sync-form input[name="name"]').type('Emby Sync');

      // Submit form
      cy.get('#add-emby-sync-modal button').click();

      // Modal should close
      cy.get('#add-emby-sync-modal').should('not.be.visible');

      // Verify new Sync element is visible
      cy.get('#emby-syncs .ui.card .header').should('contain', 'Emby Sync');
    });
  });

  describe('Jellyfin Sync Form', () => {
    beforeEach(() => {
      cy.createJellyfinConnection(true);
      cy.visit('/sync');
      cy.get('#add-jellyfin-sync').click();
    });

    it('displays all required form fields', () => {
      cy.get('#jellyfin-sync-form').within(() => {
        cy.get('input[name="interface_id"]').should('exist');
        cy.get('input[name="name"]').should('exist');
        cy.get('input[name="template_ids"]').should('exist');
        cy.get('input[name="add_as_unmonitored"]').should('exist');
        cy.get('input[name="required_tags"]').should('exist');
        cy.get('input[name="required_libraries"]').should('exist');
        cy.get('input[name="excluded_tags"]').should('exist');
        cy.get('input[name="excluded_libraries"]').should('exist');
      });
    });

    it('populates connection dropdown with available connections', () => {
      cy.selectDropdown('#add-jellyfin-sync-modal', '.dropdown[data-value="interface_id"]', 'Jellyfin');
    });

    it('submits form successfully with valid data', () => {
      // Select connection
      cy.selectDropdown('#add-jellyfin-sync-modal', '.dropdown[data-value="interface_id"]', 'Jellyfin');

      // Fill required fields
      cy.get('#add-jellyfin-sync-modal input[name="name"]').type('Jellyfin Sync');

      // Submit form
      cy.get('#add-jellyfin-sync-modal').contains('Create').click();

      // Modal should close
      cy.get('#add-jellyfin-sync-modal').should('not.be.visible');

      // Verify new Sync element is visible
      cy.get('#jellyfin-syncs .ui.card .header').should('contain', 'Jellyfin Sync');
    });
  });

  describe('Plex Sync Form', () => {
    beforeEach(() => {
      cy.createPlexConnection(true);
      cy.visit('/sync');
      cy.get('#add-plex-sync').click();
    });

    it('displays all required form fields', () => {
      cy.get('#plex-sync-form').within(() => {
        cy.get('input[name="interface_id"]').should('exist');
        cy.get('input[name="name"]').should('exist');
        cy.get('input[name="template_ids"]').should('exist');
        cy.get('input[name="add_as_unmonitored"]').should('exist');
        cy.get('input[name="required_tags"]').should('exist');
        cy.get('input[name="required_libraries"]').should('exist');
        cy.get('input[name="excluded_tags"]').should('exist');
        cy.get('input[name="excluded_libraries"]').should('exist');
      });
    });

    it('uses "Labels" terminology instead of "Tags"', () => {
      cy.get('#plex-sync-form').within(() => {
        cy.get('label').should('contain', 'Labels');
      });
    });

    it('populates connection dropdown with available connections', () => {
      cy.selectDropdown('#add-plex-sync-modal', '.dropdown[data-value="interface_id"]', 'Plex');
    });

    it('submits form successfully with valid data', () => {
      // Select connection
      cy.selectDropdown('#add-plex-sync-modal', '.dropdown[data-value="interface_id"]', 'Plex');

      // Fill required fields
      cy.get('#plex-sync-form input[name="name"]').type('Plex Sync');

      // Submit form
      cy.get('#add-plex-sync-modal button').click();

      // Modal should close
      cy.get('#add-plex-sync-modal').should('not.be.visible');

      // Verify new Sync element is visible
      cy.get('#plex-syncs .ui.card .header').should('contain', 'Plex Sync');
    });
  });

  describe('Sonarr Sync Form', () => {
    beforeEach(() => {
      cy.createSonarrConnection(true);
      cy.visit('/sync');
      cy.get('#add-sonarr-sync').click();
    });

    it('displays all required form fields', () => {
      cy.get('#sonarr-sync-form').within(() => {
        cy.get('input[name="interface_id"]').should('exist');
        cy.get('input[name="name"]').should('exist');
        cy.get('input[name="template_ids"]').should('exist');
        cy.get('input[name="add_as_unmonitored"]').should('exist');
        cy.get('input[name="required_tags"]').should('exist');
        cy.get('input[name="required_series_type"]').should('exist');
        cy.get('input[name="required_root_folders"]').should('exist');
        cy.get('input[name="downloaded_only"]').should('exist');
        cy.get('input[name="monitored_only"]').should('exist');
        cy.get('input[name="excluded_tags"]').should('exist');
        cy.get('input[name="excluded_series_type"]').should('exist');
      });
    });

    it('displays series type options', () => {
      cy.get('#add-sonarr-sync-modal [data-value="required_series_type"]').click();
      cy.get('#add-sonarr-sync-modal [data-value="required_series_type"] .menu').within(() => {
        cy.get('.item[data-value="anime"]').should('contain', 'Anime');
        cy.get('.item[data-value="daily"]').should('contain', 'Daily');
        cy.get('.item[data-value="standard"]').should('contain', 'Standard');
      });
    });

    it('allows adding custom tags and root folders', () => {
      // Add custom tag
      cy.get('#add-sonarr-sync-modal [data-value="required_tags"]').click();
      cy.get('#add-sonarr-sync-modal [data-value="required_tags"] input.search').type('custom-tag{enter}');
      cy.get('#add-sonarr-sync-modal [data-value="required_tags"] .label').should('contain', 'custom-tag');
      
      // Add custom root folder
      cy.get('#add-sonarr-sync-modal [data-value="required_root_folders"]').click();
      cy.get('#add-sonarr-sync-modal [data-value="required_root_folders"] input.search').type('/custom/path{enter}');
      cy.get('#add-sonarr-sync-modal [data-value="required_root_folders"] .label').should('contain', '/custom/path');
    });

    it('populates connection dropdown with available connections', () => {
      cy.selectDropdown('#add-sonarr-sync-modal', '.dropdown[data-value="interface_id"]', 'Sonarr');
    });

    it('submits form successfully with valid data', () => {
      // Select connection
      cy.selectDropdown('#add-sonarr-sync-modal', '.dropdown[data-value="interface_id"]', 'Sonarr');

      // Fill required fields
      cy.get('#sonarr-sync-form input[name="name"]').type('Sonarr Sync');

      // Submit form
      cy.get('#add-sonarr-sync-modal button').click();

      // Modal should close
      cy.get('#add-sonarr-sync-modal').should('not.be.visible');

      // Verify new Sync element is visible
      cy.get('#sonarr-syncs .ui.card .header').should('contain', 'Sonarr Sync');
    });
  });

  describe('Sync Management', () => {
    beforeEach(() => {
      // Create connections and syncs for testing
      cy.createEmbyConnection(true).then(() => {
        cy.createObjectAndGetId('/api/v2/sync/emby/new', {
          'name': 'Test Sync',
          'interface_id': 1,
          'add_as_unmonitored': false
        });
      });
      
      cy.visit('/sync');
    });

    it('displays existing syncs', () => {
      cy.get('#emby-syncs .ui.card').should('have.length.greaterThan', 1); // Including add card
    });

    it('shows sync information in cards', () => {
      cy.get('#emby-syncs .ui.card').not('.add').first().within(() => {
        cy.get('.header').should('contain', 'Test Sync');
        cy.get('.sync-meta').should('contain', 'Sync ID');
        cy.get('.trash.icon').should('exist');
        cy.get('.sync.icon').should('exist');
        cy.get('.edit.icon').should('exist');
      });
    });

    it('opens delete confirmation modal when clicking trash icon', () => {
      cy.get('#emby-syncs .ui.card').not('.add').first().find('.trash.icon').click();
      cy.get('#delete-sync-modal').should('be.visible');
      cy.get('#delete-sync-modal .header').should('contain', 'Delete Sync?');
    });

    it('provides delete options in confirmation modal', () => {
      cy.get('#emby-syncs .ui.card').not('.add').first().find('.trash.icon').click();
      cy.get('#delete-sync-modal').should('be.visible');

      cy.get('#delete-sync-modal [data-action="delete-sync-only"]').should('contain', 'Yes');
      cy.get('#delete-sync-modal [data-action="delete-sync-and-series"]').should('contain', 'Yes, and Delete Associated Series');
      cy.get('#delete-sync-modal .ui.green.ok.basic.inverted.button').should('contain', 'No');
    });

    it('cancels delete when clicking No', () => {
      cy.get('#emby-syncs .ui.card').not('.add').first().find('.trash.icon').click();
      cy.get('#delete-sync-modal').should('be.visible');
      cy.get('#delete-sync-modal .ui.green.ok.basic.inverted.button').click();
      cy.get('#delete-sync-modal').should('not.be.visible');
      cy.get('#emby-syncs .ui.card').should('have.length.greaterThan', 1); // Including add card
    });

    it('deletes sync when clicking Yes', () => {
      cy.get('#emby-syncs .ui.card').not('.add').first().find('.trash.icon').click();
      cy.get('#delete-sync-modal').should('be.visible');
      cy.get('#delete-sync-modal .button').contains('Yes').click();
      cy.get('#delete-sync-modal').should('not.be.visible');
      cy.get('#emby-syncs .ui.card').should('not.contain', 'Test Sync');
    });
  });

  describe('Template Selection', () => {
    beforeEach(() => {
      cy.createEmbyConnection(true);
      // Create a template for testing
      cy.createObjectAndGetId('/api/v2/templates/template/new', {
        'name': 'Test Template',
        'card_type': 'standard'
      });

      cy.visit('/sync');
      cy.get('#add-emby-sync').click();
    });

    it('allows selecting templates to apply', () => {
      // Select connection
      cy.selectDropdown('#add-emby-sync-modal', '.dropdown[data-value="interface_id"]', 'Emby');

      // Fill required name
      cy.get('#emby-sync-form input[name="name"]').type('Template Sync');

      // Select template
      cy.selectDropdown('#add-emby-sync-modal', '.dropdown[data-value="template_ids"]', 'Test Template');

      // Submit form
      cy.get('#add-emby-sync-modal button').click();

      // Modal should close
      cy.get('#add-emby-sync-modal').should('not.be.visible');
    });
  });

  describe('Accessibility and UX', () => {
    beforeEach(() => {
      cy.createEmbyConnection(true);
      cy.visit('/sync');
    });

    it('provides helpful tooltips for form fields', () => {
      cy.get('#add-emby-sync').click();

      // Check help text for various fields
      cy.get('#emby-sync-form').within(() => {
        cy.get('p.help').should('contain', 'Add the specified Template(s) to any Synced Series');
        cy.get('p.help').should('contain', 'Mark any newly added Series as Unmonitored');
        cy.get('p.help').should('contain', 'All Tags required for a Series to be Synced');
        cy.get('p.help').should('contain', 'Only Sync Series from the specified Libraries');
      });
    });
  });
});