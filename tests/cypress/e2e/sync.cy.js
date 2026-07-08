describe('Sync Page', () => {
  beforeEach(() => {
    // Reset database to ensure clean state
    cy.resetDatabase();

    // Visit the sync page
    cy.visit('/sync');
  });

  describe('Page Structure and Navigation', () => {
    it('displays the sync page with correct title', () => {
      cy.get('h1.sync-page-title').should('contain', 'Sync');
      cy.url().should('contain', '/sync');
    });

    it('shows all connection sections', () => {
      cy.createEmbyConnection(true);
      cy.createJellyfinConnection(true);
      cy.createPlexConnection(true);
      cy.createSonarrConnection(true);
      cy.reload();

      ['emby', 'jellyfin', 'plex', 'sonarr'].forEach(connection => {
        cy.get(`[data-connection="${connection}"]`).should('exist');
        cy.get(`[data-connection="${connection}"] .settings-panel-header`).should('contain', connection.charAt(0).toUpperCase() + connection.slice(1));
      });
    });

    it('only shows sections with created connections', () => {
      // Initially, no connections exist, so only the warning should be visible
      cy.get('.ui.warning.floating.message').should('exist');
      cy.get('[data-connection="emby"]').should('not.exist');
      cy.get('[data-connection="jellyfin"]').should('not.exist');
      cy.get('[data-connection="plex"]').should('not.exist');
      cy.get('[data-connection="sonarr"]').should('not.exist');

      // Create only Emby connection
      cy.createEmbyConnection(true);
      cy.reload();

      // Only Emby section should be visible
      cy.get('[data-connection="emby"]').should('exist');
      cy.get('[data-connection="jellyfin"]').should('not.exist');
      cy.get('[data-connection="plex"]').should('not.exist');
      cy.get('[data-connection="sonarr"]').should('not.exist');

      // Create Jellyfin connection as well
      cy.createJellyfinConnection(true);
      cy.reload();

      // Both Emby and Jellyfin sections should be visible
      cy.get('[data-connection="emby"]').should('exist');
      cy.get('[data-connection="jellyfin"]').should('exist');
      cy.get('[data-connection="plex"]').should('not.exist');
      cy.get('[data-connection="sonarr"]').should('not.exist');
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
      cy.get('#emby-syncs .card .header').should('contain', 'Emby Sync');
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
      cy.get('#jellyfin-syncs .card .header').should('contain', 'Jellyfin Sync');
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
      cy.get('#plex-syncs .card .header').should('contain', 'Plex Sync');
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
      cy.get('#sonarr-syncs .card .header').should('contain', 'Sonarr Sync');
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
      cy.get('#emby-syncs .card').should('have.length.greaterThan', 0);
    });

    it('shows sync information in cards', () => {
      cy.get('#emby-syncs .card').first().within(() => {
        cy.get('.header').should('contain', 'Test Sync');
        cy.get('.sync-meta').should('contain', 'Sync ID');
        cy.get('.trash.alternate.outline.icon').should('exist');
        cy.get('.sync.icon').should('exist');
        cy.get('.edit.icon').should('exist');
      });
    });

    it('opens delete confirmation modal when clicking trash icon', () => {
      cy.get('#emby-syncs .card').first().find('.sync-action-btn--delete').click();
      cy.get('#delete-sync-modal').should('be.visible');
      cy.get('#delete-sync-modal .header').should('contain', 'Delete Sync?');
    });

    it('provides delete options in confirmation modal', () => {
      cy.get('#emby-syncs .card').first().find('.sync-action-btn--delete').click();
      cy.get('#delete-sync-modal').should('be.visible');

      cy.get('#delete-sync-modal [data-action="delete-sync-only"]').should('contain', 'Yes');
      cy.get('#delete-sync-modal [data-action="delete-sync-and-series"]').should('contain', 'Yes, and Delete Associated Series');
      cy.get('#delete-sync-modal .ui.green.ok.basic.inverted.button').should('contain', 'No');
    });

    it('cancels delete when clicking No', () => {
      cy.get('#emby-syncs .card').first().find('.sync-action-btn--delete').click();
      cy.get('#delete-sync-modal').should('be.visible');
      cy.get('#delete-sync-modal .ui.green.ok.basic.inverted.button').click();
      cy.get('#delete-sync-modal').should('not.be.visible');
      cy.get('#emby-syncs .card').should('have.length.greaterThan', 0);
    });

    it('deletes sync when clicking Yes', () => {
      cy.get('#emby-syncs .card').first().find('.sync-action-btn--delete').click();
      cy.get('#delete-sync-modal').should('be.visible');
      cy.get('#delete-sync-modal .button').contains('Yes').click();
      cy.get('#delete-sync-modal').should('not.be.visible');
      cy.get('#emby-syncs .card').should('not.contain', 'Test Sync');
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

  describe('Sync Settings Persistence', () => {
    beforeEach(() => {
      cy.createEmbyConnection(true);
      cy.createJellyfinConnection(true);
      cy.createPlexConnection(true);
      cy.createSonarrConnection(true);

      cy.visit('/sync');
    });

    it('persists Emby sync settings after page reload', () => {
      // Create a sync with various settings
      cy.get('#add-emby-sync').click();

      // Select connection
      cy.selectDropdown('#add-emby-sync-modal', '.dropdown[data-value="interface_id"]', 'Emby');

      // Fill in various settings
      cy.get('#emby-sync-form input[name="name"]').type('Persistent Emby Sync');
      cy.get('#emby-sync-form input[name="add_as_unmonitored"]').click({ force: true });

      // Add required tags
      cy.get('#emby-sync-form input[name="required_tags"]').type('persistent-tag', { force: true});

      // Add required libraries
      cy.get('#emby-sync-form [data-value="required_libraries"]').click();
      cy.get('#emby-sync-form [data-value="required_libraries"]').contains('TV').click();

      // Add excluded tags
      cy.get('#emby-sync-form input[name="excluded_tags"]').type('excluded-tag', { force: true });

      // Add excluded libraries
      cy.get('#emby-sync-form [data-value="excluded_libraries"]').click();
      cy.get('#emby-sync-form [data-value="excluded_libraries"]').contains('TV 4K').click();

      // Submit form
      cy.get('#add-emby-sync-modal .actions').contains('Create').click();
      cy.get('#add-emby-sync-modal').should('not.be.visible');

      // Verify sync was created
      cy.get('#emby-syncs .card .header').should('contain', 'Persistent Emby Sync');

      // Reload the page
      cy.reload();

      // Verify sync still exists with same settings
      cy.get('#emby-syncs .card .header').should('contain', 'Persistent Emby Sync');

      // Open edit modal to verify settings persisted
      cy.get('#emby-syncs .card').first().find('.sync-action-btn--edit').click();

      // Verify settings are still there
      cy.get('.visible.sync.modal input[name="name"]').should('have.value', 'Persistent Emby Sync');
      cy.get('.visible.sync.modal input[name="add_as_unmonitored"]').should('be.checked');
      cy.get('.visible.sync.modal [data-value="required_tags"] .label').should('contain', 'persistent-tag');
      cy.get('.visible.sync.modal [data-value="required_libraries"] .label').should('contain', 'TV');
      cy.get('.visible.sync.modal [data-value="excluded_tags"] .label').should('contain', 'excluded-tag');
      cy.get('.visible.sync.modal [data-value="excluded_libraries"] .label').should('contain', 'TV 4K');
    });

    it('persists Jellyfin sync settings after page reload', () => {
      // Create a sync with various settings
      cy.get('#add-jellyfin-sync').click();

      // Select connection
      cy.selectDropdown('#add-jellyfin-sync-modal', '.dropdown[data-value="interface_id"]', 'Jellyfin');

      // Fill in various settings
      cy.get('#jellyfin-sync-form input[name="name"]').type('Persistent Jellyfin Sync');
      cy.get('#jellyfin-sync-form input[name="add_as_unmonitored"]').click({ force: true });

      // Add required tags
      cy.get('#jellyfin-sync-form input[name="required_tags"]').type('persistent-tag', { force: true});

      // Add required libraries
      cy.get('#jellyfin-sync-form [data-value="required_libraries"]').click();
      cy.get('#jellyfin-sync-form [data-value="required_libraries"]').contains('TV').click();

      // Add excluded tags
      cy.get('#jellyfin-sync-form input[name="excluded_tags"]').type('excluded-tag', { force: true });

      // Add excluded libraries
      cy.get('#jellyfin-sync-form [data-value="excluded_libraries"]').click();
      cy.get('#jellyfin-sync-form [data-value="excluded_libraries"]').contains('TV 4K').click();

      // Submit form
      cy.get('#add-jellyfin-sync-modal .actions').contains('Create').click();
      cy.get('#add-jellyfin-sync-modal').should('not.be.visible');

      // Verify sync was created
      cy.get('#jellyfin-syncs .card .header').should('contain', 'Persistent Jellyfin Sync');

      // Reload the page
      cy.reload();

      // Verify sync still exists with same settings
      cy.get('#jellyfin-syncs .card .header').should('contain', 'Persistent Jellyfin Sync');

      // Open edit modal to verify settings persisted
      cy.get('#jellyfin-syncs .card').first().find('.sync-action-btn--edit').click();

      // Verify settings are still there
      cy.get('.visible.sync.modal input[name="name"]').should('have.value', 'Persistent Jellyfin Sync');
      cy.get('.visible.sync.modal input[name="add_as_unmonitored"]').should('be.checked');
      cy.get('.visible.sync.modal [data-value="required_tags"] .label').should('contain', 'persistent-tag');
      cy.get('.visible.sync.modal [data-value="required_libraries"] .label').should('contain', 'TV');
      cy.get('.visible.sync.modal [data-value="excluded_tags"] .label').should('contain', 'excluded-tag');
      cy.get('.visible.sync.modal [data-value="excluded_libraries"] .label').should('contain', 'TV 4K');
    });

    it('persists Plex sync settings after page reload', () => {
      // Create a sync with various settings
      cy.get('#add-plex-sync').click();

      // Select connection
      cy.selectDropdown('#add-plex-sync-modal', '.dropdown[data-value="interface_id"]', 'Plex');

      // Fill in various settings
      cy.get('#plex-sync-form input[name="name"]').type('Persistent Plex Sync');
      cy.get('#plex-sync-form input[name="add_as_unmonitored"]').click({ force: true });

      // Add required labels (Plex uses "Labels" instead of "Tags")
      cy.get('#plex-sync-form input[name="required_tags"]').type('persistent-tag', { force: true});

      // Add required libraries
      cy.get('#plex-sync-form [data-value="required_libraries"]').click();
      cy.get('#plex-sync-form [data-value="required_libraries"]').contains('TV').click();

      // Add excluded tags
      cy.get('#plex-sync-form input[name="excluded_tags"]').type('excluded-tag', { force: true });

      // Add excluded libraries
      cy.get('#plex-sync-form [data-value="excluded_libraries"]').click();
      cy.get('#plex-sync-form [data-value="excluded_libraries"]').contains('TV 4K').click();

      // Submit form
      cy.get('#add-plex-sync-modal .actions').contains('Create').click();
      cy.get('#add-plex-sync-modal').should('not.be.visible');

      // Verify sync was created
      cy.get('#plex-syncs .card .header').should('contain', 'Persistent Plex Sync');

      // Reload the page
      cy.reload();

      // Verify sync still exists with same settings
      cy.get('#plex-syncs .card .header').should('contain', 'Persistent Plex Sync');

      // Open edit modal to verify settings persisted
      cy.get('#plex-syncs .card').first().find('.sync-action-btn--edit').click();

      // Verify settings are still there
      cy.get('.visible.sync.modal input[name="name"]').should('have.value', 'Persistent Plex Sync');
      cy.get('.visible.sync.modal input[name="add_as_unmonitored"]').should('be.checked');
      cy.get('.visible.sync.modal [data-value="required_tags"] .label').should('contain', 'persistent-tag');
      cy.get('.visible.sync.modal [data-value="required_libraries"] .label').should('contain', 'TV');
      cy.get('.visible.sync.modal [data-value="excluded_tags"] .label').should('contain', 'excluded-tag');
      cy.get('.visible.sync.modal [data-value="excluded_libraries"] .label').should('contain', 'TV 4K');
    });

    it('persists Sonarr sync settings after page reload', () => {
      // Create a sync with various settings
      cy.get('#add-sonarr-sync').click();

      // Select connection
      cy.selectDropdown('#add-sonarr-sync-modal', '.dropdown[data-value="interface_id"]', 'Sonarr');

      // Fill in various settings
      cy.get('#sonarr-sync-form input[name="name"]').type('Persistent Sonarr Sync');
      cy.get('#sonarr-sync-form input[name="add_as_unmonitored"]').click({ force: true });
      cy.get('#sonarr-sync-form input[name="downloaded_only"]').click({ force: true });
      cy.get('#sonarr-sync-form input[name="monitored_only"]').click({ force: true });

      // Add required tags
      cy.get('#sonarr-sync-form [data-value="required_tags"]').click();
      cy.get('#sonarr-sync-form [data-value="required_tags"] .menu').contains('star wars').click();
      // Click outside dropdown to close it
      cy.get('#sonarr-sync-form .header').contains('Filters').click();

      // Select required series type
      cy.get('#sonarr-sync-form [data-value="required_series_type"]').click();
      cy.get('#sonarr-sync-form [data-value="required_series_type"] .menu').contains('Anime').click();

      // Add required root folders
      cy.get('#sonarr-sync-form input[name="required_root_folders"]').type('/example/folder/', { force: true });

      // Add excluded tags
      cy.get('#sonarr-sync-form input[name="excluded_tags"]').type('excluded-tag', { force: true });

      // Select excluded series type
      cy.get('#sonarr-sync-form [data-value="excluded_series_type"]').click();
      cy.get('#sonarr-sync-form [data-value="excluded_series_type"] .menu').contains('Daily').click();

      // Submit form
      cy.get('#add-sonarr-sync-modal button').click();
      cy.get('#add-sonarr-sync-modal').should('not.be.visible');

      // Verify sync was created
      cy.get('#sonarr-syncs .card .header').should('contain', 'Persistent Sonarr Sync');

      // Reload the page
      cy.reload();

      // Verify sync still exists with same settings
      cy.get('#sonarr-syncs .card .header').should('contain', 'Persistent Sonarr Sync');

      // Open edit modal to verify settings persisted
      cy.get('#sonarr-syncs .card').first().find('.sync-action-btn--edit').click();

      // Verify settings are still there
      cy.get('.visible.sync.modal input[name="name"]').should('have.value', 'Persistent Sonarr Sync');
      cy.get('.visible.sync.modal input[name="add_as_unmonitored"]').should('be.checked');
      cy.get('.visible.sync.modal [data-value="required_tags"] .label').should('contain', 'star wars');
      cy.get('.visible.sync.modal [data-value="required_series_type"]').should('contain', 'Anime');
      cy.get('.visible.sync.modal [data-value="required_root_folders"] .label').should('contain', '/example/folder/');
      cy.get('.visible.sync.modal input[name="downloaded_only"]').should('be.checked');
      cy.get('.visible.sync.modal input[name="monitored_only"]').should('be.checked');
      cy.get('.visible.sync.modal [data-value="excluded_tags"] .label').should('contain', 'excluded-tag');
      cy.get('.visible.sync.modal [data-value="excluded_series_type"]').should('contain', 'Daily');
    });

    it('persists template selection in sync settings', () => {
      // Create a template for testing
      cy.createObjectAndGetId('/api/v2/templates/template/new', {
        'name': 'Test Template 1',
        'card_type': 'standard'
      });
      // Create a template for testing
      cy.createObjectAndGetId('/api/v2/templates/template/new', {
        'name': 'Test Template 2',
        'card_type': 'anime'
      });
      cy.visit('/sync');

      // Create a sync with template selection
      cy.get('#add-emby-sync').click();

      // Select connection
      cy.selectDropdown('#add-emby-sync-modal', '.dropdown[data-value="interface_id"]', 'Emby');

      // Fill required fields
      cy.get('#emby-sync-form input[name="name"]').type('Template Sync');

      // Select Templates
      cy.selectDropdown('#add-emby-sync-modal', '.dropdown[data-value="template_ids"]', 'Test Template 2');
      cy.selectDropdown('#add-emby-sync-modal', '.dropdown[data-value="template_ids"]', 'Test Template 1');

      // Submit form
      cy.get('#add-emby-sync-modal button').click();
      cy.get('#add-emby-sync-modal').should('not.be.visible');

      // Verify sync was created
      cy.get('#emby-syncs .card .header').should('contain', 'Template Sync');

      // Reload the page
      cy.reload();

      // Verify sync still exists
      cy.get('#emby-syncs .card .header').should('contain', 'Template Sync');

      // Open edit modal to verify template selection persisted
      cy.get('#emby-syncs .card').first().find('.sync-action-btn--edit').click();

      // Verify Templates is still selected
      cy.get('.visible.sync.modal [data-value="template_ids"] .label').first().should('contain', 'Test Template 2');
      cy.get('.visible.sync.modal [data-value="template_ids"] .label').last().should('contain', 'Test Template 1');
    });
  });
});
