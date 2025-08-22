describe('Add Series Page', () => {
  beforeEach(() => {
    // Reset database and create test connections
    cy.resetDatabase();
    cy.createEmbyConnection(true);
    cy.createJellyfinConnection(true);
    cy.createPlexConnection(true);
    cy.createSonarrConnection(true);
    cy.createTMDbConnection(true);
    cy.createTVDbConnection(true);

    // Create some test templates and libraries
    cy.createObjectAndGetId('/api/v2/templates/template/new', {
      'name': 'Test Template 1',
      'card_type': 'standard'
    });

    cy.createObjectAndGetId('/api/v2/templates/template/new', {
      'name': 'Test Template 2', 
      'card_type': 'anime'
    });

    // Visit the add series page
    cy.visit('/add');
  });

  describe('Page Structure and Navigation', () => {
    it('should display the correct page title and sections', () => {
      cy.get('h3').should('contain', 'Browse Series');
      cy.get('h3').should('contain', 'Browse Blueprints');
      cy.get('#series-search').should('be.visible');
      cy.get('#blueprint-search').should('be.visible');
    });

    it('should show help information for both sections', () => {
      // Series help
      cy.get('#series-search .ui.info.message').should('be.visible');
      cy.get('#series-search .ui.info.message').should('contain', 'Search Series');
      cy.get('#series-search .ui.info.message').should('contain', 'Configure Settings');
      
      // Blueprint help
      cy.get('#blueprint-search .ui.info.message').should('be.visible');
      cy.get('#blueprint-search .ui.info.message').should('contain', 'Browse Blueprints');
      cy.get('#blueprint-search .ui.info.message').should('contain', 'Import');
    });
  });

  describe('Series Search Functionality', () => {
    it('should have all required form fields', () => {
      // Search query field
      cy.get('#search-query').should('be.visible');
      cy.get('#search-query').should('have.attr', 'placeholder', 'Series Name');
      cy.get('#search-query').should('have.attr', 'autofocus');

      // Connection dropdown
      cy.get('[data-value="interface_id"]').should('be.visible');

      // Libraries dropdown
      cy.get('#libraries-dropdown').should('be.visible');

      // Templates dropdown
      cy.get('#templates-dropdown').should('be.visible');
    });

    it('should populate connection dropdown with available connections', () => {
      cy.get('[data-value="interface_id"]').click();
      cy.get('[data-value="interface_id"] .menu').should('be.visible');
      cy.get('[data-value="interface_id"] .menu .item').should('contain', 'Emby');
      cy.get('[data-value="interface_id"] .menu .item').should('contain', 'Jellyfin');
      cy.get('[data-value="interface_id"] .menu .item').should('contain', 'Plex');
      cy.get('[data-value="interface_id"] .menu .item').should('contain', 'Sonarr');
      cy.get('[data-value="interface_id"] .menu .item').should('contain', 'TMDb');
      cy.get('[data-value="interface_id"] .menu .item').should('contain', 'TVDb');
    });

    it('should populate libraries dropdown', () => {
      cy.get('#libraries-dropdown').click();
      cy.get('#libraries-dropdown .menu').should('be.visible');
      cy.get('#libraries-dropdown .menu .item').should('contain', 'Anime');
      cy.get('#libraries-dropdown .menu .item').should('contain', 'TV');
      cy.get('#libraries-dropdown .menu .item').should('contain', 'TV 4K');
      cy.get('#libraries-dropdown .menu .item').should('contain', 'Emby');
      cy.get('#libraries-dropdown .menu .item').should('contain', 'Jellyfin');
      cy.get('#libraries-dropdown .menu .item').should('contain', 'Plex');
    });

    it('should populate templates dropdown', () => {
      cy.get('#templates-dropdown').click();
      cy.get('#templates-dropdown .menu').should('be.visible');
      cy.get('#templates-dropdown .menu .item').should('contain', 'Test Template 1');
      cy.get('#templates-dropdown .menu .item').should('contain', 'Test Template 2');
    });

    it('should have search and show missing buttons', () => {
      cy.get('#startSearch').should('be.visible');
      cy.get('#startSearch').should('contain', 'Search Series');
      cy.get('#startSearch').should('have.class', 'primary');
      
      cy.get('button').contains('Show Missing').should('be.visible');
      cy.get('button').contains('Show Missing').should('have.class', 'red');
    });

    it('should show search results section when searching', () => {
      // Select a connection first
      cy.get('[data-value="interface_id"]').click();
      cy.get('[data-value="interface_id"] .menu .item').contains('Sonarr').click();
      
      // Type a search query
      cy.get('#search-query').type('Test Series');
      
      // Click search button
      cy.get('#startSearch').click();
      
      // Search results section should be visible
      cy.get('#search-results').should('be.visible');
    });
  });

  describe('Blueprint Search Functionality', () => {
    it('should have blueprint filter form fields', () => {
      // Filter by name
      cy.get('#blueprint-filter').scrollIntoView().should('be.visible');
      cy.get('#blueprint-filter').should('have.attr', 'placeholder', 'Series Name');
      
      // Sort order dropdown
      cy.get('#blueprint-sort').should('be.visible');
      cy.get('#blueprint-sort option[value="date"]').should('be.selected');
      cy.get('#blueprint-sort option[value="name"]').should('exist');
      
      // Checkboxes
      cy.get('[data-value="include_missing_series"] input[type="checkbox"]').should('exist');
      cy.get('[data-value="included_imported"] input[type="checkbox"]').should('exist');
    });

    it('should have browse blueprints button', () => {
      cy.get('[data-action="browse-blueprints"]').scrollIntoView().should('be.visible');
      cy.get('[data-action="browse-blueprints"]').should('contain', 'Browse Blueprints');
      cy.get('[data-action="browse-blueprints"]').should('have.class', 'green');
    });

    it('should show blueprint results when browsing', () => {
      // Click browse blueprints button
      cy.get('[data-action="browse-blueprints"]').click();

      // Results section should be visible
      cy.get('#all-blueprint-results').should('be.visible');
    });

    it('should show pagination when there are many results', () => {
      // Click browse blueprints button
      cy.get('[data-action="browse-blueprints"]').click();
      cy.get('#all-blueprint-results').should('be.visible');

      // Pagination should be visible
      cy.get('#blueprint-pagination').scrollIntoView().should('be.visible');
    });
  });

  describe('Form Interactions and Validation', () => {
    it('should allow selecting multiple libraries', () => {
      // Select a connection first
      cy.get('[data-value="interface_id"]').click();
      cy.get('[data-value="interface_id"] .menu .item').first().click();
      
      // Click libraries dropdown
      cy.get('#libraries-dropdown').click();
      cy.get('#libraries-dropdown .menu').should('be.visible');
      cy.get('#libraries-dropdown .menu .item').contains('Anime').click();
      cy.get('#libraries-dropdown .menu .item').contains('TV').click();

      // Should have two selected libraries
      cy.get('#libraries-dropdown a.label').should('have.length', 2);
    });

    it('should allow selecting multiple templates', () => {
      // Click templates dropdown
      cy.get('#templates-dropdown').click();
      cy.get('#templates-dropdown .menu').should('be.visible');
      cy.get('#templates-dropdown .menu .item').first().click();
      cy.get('#templates-dropdown .menu .item').last().click();

      // Should be able to select multiple items
      cy.get('#templates-dropdown a.label').should('have.length', 2);
    });
  });

  describe('Search Results Display', () => {
    it('should show search results with proper structure', () => {
      // Select a connection
      cy.get('[data-value="interface_id"]').click();
      cy.get('[data-value="interface_id"] .menu .item').contains('Sonarr').click();

      // Search for something
      cy.get('#search-query').type('Test Series');
      cy.get('#startSearch').click();

      // Results should be visible
      cy.get('#search-results').should('be.visible');

      // Validate dummy results
      cy.get('#search-results .ui.card').should('have.length', 2);
      cy.get('#search-results .ui.card .image').should('have.length', 2);
      cy.get('#search-results .ui.card .image img').should('have.length', 2);
      cy.get('#search-results .ui.card .image img').first().should('have.attr', 'src').should('include', '/public/styles/art.jpg');
      cy.get('#search-results .ui.card .image img').last().should('have.attr', 'src').should('include', '/public/styles/unique.jpg');
      cy.get('#search-results .ui.card .content .header').should('have.length', 2);
      cy.get('#search-results .ui.card .content .header').should('contain', 'Test Series 1');
      cy.get('#search-results .ui.card .content .header').should('contain', 'Test Series 2');
    });

    it('should show blueprint results with proper structure', () => {
      // Click browse blueprints
      cy.get('[data-action="browse-blueprints"]').click();
      
      // Results should be visible
      cy.get('#all-blueprint-results').should('be.visible');
      cy.get('#all-blueprint-results').should('have.class', 'ui');
      cy.get('#all-blueprint-results').should('have.class', 'three');
      cy.get('#all-blueprint-results').should('have.class', 'stackable');
      cy.get('#all-blueprint-results').should('have.class', 'raised');
      cy.get('#all-blueprint-results').should('have.class', 'cards');
    });
  });

  describe('Error States and Edge Cases', () => {
    it('should show warning when no connections are available', () => {
      // Reset to remove connections
      cy.resetDatabase();
      cy.visit('/add');
      
      // Should show warning message
      cy.get('.ui.warning.message').should('be.visible');
      cy.get('.ui.warning.message').should('contain', 'No Connections Available');
      cy.get('.ui.warning.message').should('contain', 'Please add a Connection');
      cy.get('.ui.warning.message a[href="/connections"]').should('exist');

      // Should link to connections page
      cy.get('.ui.warning.message a[href="/connections"]').should('exist');
      cy.get('.ui.warning.message a[href="/connections"]').should('contain', 'Connections');
    });

    it('should handle empty search queries', () => {
      // Select a connection
      cy.get('[data-value="interface_id"]').click();
      cy.get('[data-value="interface_id"] .menu .item').first().click();
      
      // Try to search with empty query
      cy.get('#startSearch').click();
      
      cy.get('#search-results').should('not.be.visible');
    });
  });

  describe('Responsive Design and Accessibility', () => {
    it('should have proper form labels and help text', () => {
      // Check labels
      cy.get('label[for="search-query"]').should('contain', 'Series Name');
      cy.get('label[for="libraries-dropdown"]').should('contain', 'Libraries');
      cy.get('label[for="templates-dropdown"]').should('contain', 'Templates');
      cy.get('label[for="blueprint-filter"]').should('contain', 'Filter by Name');
      cy.get('label[for="blueprint-sort"]').should('contain', 'Sort Order');
      
      // Check help text
      cy.get('#libraries-dropdown').parent().find('.help').should('contain', 'Select which Libraries');
      cy.get('#templates-dropdown').parent().find('.help').should('contain', 'Select which Templates');
      cy.get('[data-value="include_missing_series"]').parent().find('.help').should('contain', 'Exclude Blueprints');
      cy.get('[data-value="included_imported"]').parent().find('.help').should('contain', 'Include Blueprints');
    });

    it('should have proper button types and icons', () => {
      // Search button
      cy.get('#startSearch').should('have.attr', 'type', 'button');
      cy.get('#startSearch i.search.icon').should('exist');
      
      // Show missing button
      cy.get('button').contains('Show Missing').should('have.attr', 'type', 'button');
      cy.get('button').contains('Show Missing').find('i.exclamation.triangle.icon').should('exist');
      
      // Browse blueprints button
      cy.get('[data-action="browse-blueprints"]').should('have.attr', 'type', 'button');
      cy.get('[data-action="browse-blueprints"]').find('i.sitemap.icon').should('exist');
    });
  });

  describe('Blueprint Interactions', () => {
    it('should show blueprint actions popup when ellipsis is clicked', () => {
      // Click browse blueprints to get results
      cy.get('[data-action="browse-blueprints"]').click();
      
      // Look for blueprint cards with actions
      cy.get('#all-blueprint-results').should('be.visible');
      
      // If there are blueprint cards, test the actions popup
      cy.get('#all-blueprint-results .ui.raised.blueprint.card').then(($cards) => {
        if ($cards.length > 0) {
          // Click the ellipsis icon on the first card
          cy.wrap($cards.first()).find('[data-action="actions"]').click();
          
          // Actions popup should be visible
          cy.get('[data-label="actions-popup"]').should('be.visible');
          cy.get('[data-label="actions-popup"]').should('contain', 'Import');
          cy.get('[data-label="actions-popup"]').should('contain', 'Hide');
          cy.get('[data-label="actions-popup"]').should('contain', 'Filter Series');
        }
      });
    });

    it('should allow filtering blueprints by creator', () => {
      // Test the by:username filter functionality mentioned in help
      cy.get('#blueprint-filter').type('by:CollinHeist');
      cy.get('#blueprint-filter').should('have.value', 'by:CollinHeist');

      // Click browse blueprints
      cy.get('[data-action="browse-blueprints"]').click();

      // Blueprint cards should be visible
      cy.get('#all-blueprint-results').should('be.visible');

      // Blueprint cards should contain the creator's name
      cy.get('#all-blueprint-results .ui.raised.blueprint.card .content .meta').should('contain', 'CollinHeist');
    });

    it('should show blueprint sets when available', () => {
      cy.get('#blueprint-filter').type('Legend of the Galactic Heroes');
      // Click browse blueprints
      cy.get('[data-action="browse-blueprints"]').click();
      
      // Find CollinHeist's blueprint, is associated with a Set
      cy.get('#all-blueprint-results .ui.raised.blueprint.card .content .meta').contains('CollinHeist').get('[data-label="set-count"]').first().click();

      // Sets should be visible, 2 Blueprints in this one
      cy.get('#blueprint-sets').should('be.visible');
      cy.get('#blueprint-sets .ui.raised.blueprint.card').should('have.length', 2);
      cy.get('#blueprint-sets .ui.raised.blueprint.card .content .header').should('contain', 'Legend of the Galactic Heroes');
      cy.get('#blueprint-sets .ui.raised.blueprint.card .content .header').should('contain', 'Legend of the Galactic Heroes');
    });
  });

  describe('Search and Series Addition', () => {
    it('should search and properly display results', () => {
      // Select TMDb connection
      cy.get('[data-value="interface_id"]').click();
      cy.get('[data-value="interface_id"] .menu .item').contains('TMDb').click();

      // Search for "Mr. Robot", this is hard-coded in the backend
      cy.get('#search-query').type('Mr. Robot');
      cy.get('#startSearch').click();

      // Should show search results
      // Should display exactly 2 results
      cy.get('#search-results').should('be.visible');
      cy.get('#search-results .ui.card').should('have.length', 2);
      
      // First result should be the main series
      cy.get('#search-results .ui.card').first().within(() => {
        cy.get('.header').should('contain', 'Mr. Robot');
        cy.get('.meta').should('contain', '2015');
        cy.get('.meta').should('contain', 'Ended');
        cy.get('.meta').should('contain', 'tmdb:62560');
        cy.get('.meta').should('contain', 'tvdb:289590');
        cy.get('.meta').should('contain', 'imdb:tt4158110');
        cy.get('.description p')
          .should('contain', 'A contemporary and culturally resonant')
          .should('contain', 'bring down corporate America.');
        cy.get('.image img').should('have.attr', 'src').should('include', 'https://image.tmdb.org/t/p/original/kv1nRqgebSsREnd7vdC2pSGjpLo.jpg');
      });

      // Second (last) result should be the after show
      cy.get('#search-results .ui.card').last().within(() => {
        cy.get('.header').should('contain', 'Mr. Robot Digital After Show');
        cy.get('.meta').should('contain', '2016');
        cy.get('.meta').should('contain', 'Ongoing');
        cy.get('.meta').should('contain', 'tmdb:67088');
        cy.get('.meta').should('contain', 'tvdb:338622');
        cy.get('.meta').should('contain', 'imdb:tt6137444');
        cy.get('.description p')
          .should('contain', 'A live weekly online series')
          .should('contain', 'artistic and technological perspective.');
        cy.get('.image img').should('have.attr', 'src').should('include', 'https://image.tmdb.org/t/p/original/1BS8oN0AbWnOWOPLv49gfwrrpO2.jpg');
      });
    });

    it('should add a series by clicking the card', () => {
      // Select TMDb connection
      cy.get('[data-value="interface_id"]').click();
      cy.get('[data-value="interface_id"] .menu .item').contains('TMDb').click();
      
      // Select some libraries
      cy.get('#libraries-dropdown').click();
      cy.get('#libraries-dropdown .menu .item').contains('TV').click();
      cy.get('#libraries-dropdown .menu .item').contains('TV 4K').click();
      
      // Select some templates
      cy.get('#templates-dropdown').click();
      cy.get('#templates-dropdown .menu .item').first().click();
      cy.get('#templates-dropdown .menu .item').last().click();

      // Search for Mr. Robot
      cy.get('#search-query').type('Mr. Robot');
      cy.get('#startSearch').click();

      // Intercept API call
      cy.intercept('POST', '/api/v2/series/new').as('addSeries');

      // Wait for results and click the first card
      cy.get('#search-results .ui.card').first().should('be.visible');
      cy.get('#search-results .ui.card').first().click();

      // Should show success message
      cy.wait('@addSeries').then((interception) => {
        expect(interception.response.statusCode).to.eq(200);
      });
    });

    it('should handle adding a series that already exists', () => {
      // First, add the series
      cy.get('[data-value="interface_id"]').click();
      cy.get('[data-value="interface_id"] .menu .item').contains('TMDb').click();

      cy.get('#libraries-dropdown').click();
      cy.get('#libraries-dropdown .menu .item').contains('TV').click();

      cy.get('#templates-dropdown').click();
      cy.get('#templates-dropdown .menu .item').first().click();

      cy.get('#search-query').type('Mr. Robot');
      cy.get('#startSearch').click();

      cy.get('#search-results .ui.card').first().click();

      // Now try to add the same series again
      cy.get('#search-query').clear().type('Mr. Robot');
      cy.get('#startSearch').click();

      // First result should be disabled, second should be enabled
      cy.get('#search-results .ui.card').first().should('have.class', 'disabled');
      cy.get('#search-results .ui.card').last().should('not.have.class', 'disabled');
    });

    it('should add a series and verify library/template assignments work', () => {
      // Select TMDb connection
      cy.get('[data-value="interface_id"]').click();
      cy.get('[data-value="interface_id"] .menu .item').contains('TMDb').click();

      // Select specific libraries
      cy.get('#libraries-dropdown').click();
      cy.get('#libraries-dropdown .menu .item').contains('TV').click();
      cy.get('#libraries-dropdown .menu .item').contains('TV 4K').click();
      cy.get('#libraries-dropdown .menu .item').contains('Anime').click();

      // Select specific templates
      cy.get('#templates-dropdown').click();
      cy.get('#templates-dropdown .menu .item').contains('Test Template 2').click();
      cy.get('#templates-dropdown .menu .item').contains('Test Template 1').click();

      // Search for a series
      cy.get('#search-query').type('Mr. Robot');
      cy.get('#startSearch').click();
      cy.get('#search-results').should('be.visible');

      // Intercept the series creation API call
      cy.intercept('POST', '/api/v2/series/new').as('createSeries');

      // Click on the first result to add the series
      cy.get('#search-results .ui.card').first().click();

      // Wait for series creation
      cy.wait('@createSeries').then((interception) => {
        expect(interception.response.statusCode).to.eq(200);

        const seriesId = interception.response.body.id;
        expect(seriesId).to.exist;

        // Navigate to the series page to verify assignments
        cy.visit(`/series/${seriesId}`);

        // Verify the series page loads
        cy.url().should('contain', `/series/${seriesId}`);

        // Check that the selected libraries are assigned
        cy.get('.dropdown[data-value="libraries"]').should('contain', 'TV');
        cy.get('.dropdown[data-value="libraries"]').should('contain', 'TV 4K');
        cy.get('.dropdown[data-value="libraries"]').should('contain', 'Anime');

        // Check that the selected templates are assigned
        cy.get('.menu .item').contains('Card Configuration').click();
        cy.get('.dropdown[data-value="template_ids"] .label').first().should('contain', 'Test Template 2');
        cy.get('.dropdown[data-value="template_ids"] .label').last().should('contain', 'Test Template 1');
      });
    });
  });

  describe('Blueprint Functionality', () => {
    it('should import a blueprint successfully', () => {
      // Browse blueprints
      cy.get('#blueprint-filter').type('Mr. Robot');
      cy.get('[data-action="browse-blueprints"]').click();

      // Wait for results
      cy.get('#all-blueprint-results').should('be.visible');

      // Intercept API call
      cy.intercept('POST', '/api/v2/blueprints/import/blueprint/*').as('importBlueprint');

      // Get first Blueprint, import it
      cy.get('#all-blueprint-results .ui.raised.blueprint.card').first().within(() => {
        cy.get('[data-action="actions"]').click();
        cy.get('[data-label="actions-popup"]').contains('Import').click();
      });

      // Wait for import to complete
      cy.wait('@importBlueprint').then((interception) => {
        expect(interception.response.statusCode).to.eq(201);

        // Search for the Series and navigate to the page
        cy.get('#search-bar input').type('Mr. Robot');
        cy.get('#search-bar .results').should('be.visible');
        cy.get('#search-bar .results .result').first().click();

        cy.url().should('contain', Cypress.config('baseUrl') + '/series/')
      });
    });

    it('should hide a blueprint and verify it is removed', () => {
      // Browse blueprints for Mr. Robot
      cy.get('#blueprint-filter').clear().type('Mr. Robot');
      cy.get('[data-action="browse-blueprints"]').click();

      // Wait for results
      cy.get('#all-blueprint-results').should('be.visible');

      // Get the count of blueprints before hiding
      cy.get('#all-blueprint-results .ui.raised.blueprint.card').then(($cards) => {
        const initialCount = $cards.length;
        expect(initialCount).to.be.greaterThan(0);

        // Intercept the hide API call
        cy.intercept('PUT', '/api/v2/blueprints/blacklist/*').as('hideBlueprint');

        // Click the ellipsis icon on the first card and hide it
        cy.get('#all-blueprint-results .ui.raised.blueprint.card').first().within(() => {
          cy.get('[data-action="actions"]').click();
          cy.get('[data-label="actions-popup"]').contains('Hide').click();
        });

        // Wait for hide API call to complete
          cy.wait('@hideBlueprint').then((interception) => {
            expect(interception.response.statusCode).to.eq(200);
          });

        // Verify the blueprint is removed from the page
        cy.get('#all-blueprint-results .ui.raised.blueprint.card').should('have.length', initialCount - 1);

        // Reload the page
        cy.reload();

        // Browse blueprints again
        cy.get('#blueprint-filter').clear().type('Mr. Robot');
        cy.get('[data-action="browse-blueprints"]').click();

        // Wait for results
        cy.get('#all-blueprint-results').should('be.visible');

        // Verify the hidden blueprint is still not visible after reload
        cy.get('#all-blueprint-results .ui.raised.blueprint.card').should('have.length', initialCount - 1);
      });
    });
  });
});
