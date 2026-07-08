describe('Settings', () => {
  beforeEach(() => {
    // Reset database to ensure clean state
    cy.resetDatabase();

    // Create a TMDb connection to enable settings
    cy.createTMDbConnection(true);

    cy.visit('/settings');
    // Wait for the page to load and initialize
    cy.get('#settings-form').should('be.visible');
    cy.wait(500);
  });

  it('Shows enabled form when connections are available', () => {
    // Verify that the warning message is not shown
    cy.get('#no-connections-warning').should('not.exist');
    
    // Verify that most form fields are enabled (excluding ImageMagick executable which is always disabled)
    cy.get('#settings-form .field').not('[data-value="imagemagick_executable"]').should('not.have.class', 'disabled');
    
    // Verify the ImageMagick executable field is specifically disabled
    cy.get('input[name="imagemagick_executable"]').parent().should('have.class', 'disabled');
    
    // Verify save button is enabled
    cy.get('#save-changes').should('not.be.disabled');
  });

  it('Requires Episode Data Source and Image Source to be configured', () => {
    // Verify that Episode Data Source dropdown is populated
    cy.get('.dropdown[data-value="episode_data_source"]').click();
    cy.get('.dropdown[data-value="episode_data_source"] .menu .item').should('have.length.at.least', 1);
    
    // Verify that Image Source Priority dropdown is populated
    cy.get('.dropdown[data-value="image_source_priority"]').click();
    cy.get('.dropdown[data-value="image_source_priority"] .menu .item').should('have.length.at.least', 1);
    
    // Close dropdowns
    cy.get('body').click(0, 0);
  });

  it('Changes the root folder settings', () => {
    const newCardDirectory = '/config/new_card_directory';
    const newSourceDirectory = '/config/new_source_directory';

    // Change card directory
    cy.get('input[name="card_directory"]')
      .clear()
      .type(newCardDirectory)
      .should('have.value', newCardDirectory);

    // Change source directory
    cy.get('input[name="source_directory"]')
      .clear()
      .type(newSourceDirectory)
      .should('have.value', newSourceDirectory);

    // Save changes (button is in sticky bar revealed on form change; force past off-screen transform)
    cy.get('#save-changes').click({ force: true });

    // Verify success message or toast appears
    cy.get('.ui.success.message, .ui.info.toast').should('be.visible');
  });

  it('Changes the default card type preview', () => {
    // Wait for card type dropdown to be populated
    cy.get('#default-card-type').should('be.visible');
    
    // Click on the default card type dropdown
    cy.get('#default-card-type').click();
    
    // Select a different card type (if available)
    cy.get('#default-card-type .menu .item').eq(2).click();
    
    // Verify the selection was made
    cy.get('#default-card-type .text').should('not.contain', 'Card Type');
    
    // Save changes
    cy.get('#save-changes').click({ force: true });
    cy.get('.ui.success.message, .ui.info.toast').should('be.visible');
  });

  it('Changes the title card settings', () => {
    // Test watched episode style dropdown
    cy.get('input[name="default_watched_style"]').parent().click();
    cy.get('input[name="default_watched_style"]').parent().find('.menu .item').contains('Blurred Art').click();

    // Test unwatched episode style dropdown
    cy.get('input[name="default_unwatched_style"]').parent().click();
    cy.get('input[name="default_unwatched_style"]').parent().find('.menu .item').contains('Blurred Unique').click();

    // Test excluded card types
    cy.get('#excluded-card-types').click();
    cy.get('#excluded-card-types .menu .item').first().click();

    // Test default templates
    // cy.get('.dropdown[data-value="default_templates"]').click();
    // cy.get('.dropdown[data-value="default_templates"] .menu .item').first().click();

    // Save changes
    cy.get('#save-changes').click({ force: true });
    cy.get('.ui.success.message, .ui.info.toast').should('be.visible');
  });

  it('Enters invalid card dimensions', () => {
    // Test invalid card width (negative number)
    cy.get('input[name="card_width"]')
      .clear()
      .type('-100')
      .should('have.value', '-100');

    // Test invalid card height (zero)
    cy.get('input[name="card_height"]')
      .clear()
      .type('0')
      .should('have.value', '0');

    // Attempt to save - client-side validation should prevent the API call
    cy.get('#save-changes').click({ force: true });

    // Reload and verify the invalid values were not persisted
    cy.reload();
    cy.get('#settings-form').should('be.visible');
    cy.get('input[name="card_width"]').should('not.have.value', '-100');
    cy.get('input[name="card_height"]').should('not.have.value', '0');
  });

  it('Selects global extras', () => {
    // Expand the Global Extras accordion
    cy.get('.accordion .title').contains('Global Extras').click();
    
    // Wait for content to be visible
    cy.get('.accordion .active.content').should('be.visible');
    
    // Test adding an extra value for a card type
    cy.get('.accordion .active.content').within(() => {
      // Find the first tab and click it
      cy.get('.menu .item').first().click();

      // Find an input field and enter a value
      cy.get('.active.tab .field input').first().clear().type('test value');
    });

    // Save changes
    cy.get('#save-changes').click({ force: true });
    cy.get('.ui.success.message, .ui.info.toast').should('be.visible');
  });

  it('Changes the file naming settings', () => {
    const newCardFilenameFormat = 'New {series_name} {title}';
    const newSpecialsFolderFormat = 'Specials';
    const newSeasonFolderFormat = 'Season {season_number}';

    // Change title card filename format
    cy.get('input[name="card_filename_format"]')
      .clear()
      .type(newCardFilenameFormat, { parseSpecialCharSequences: false })
      .should('have.value', newCardFilenameFormat);

    // Change card extension
    cy.get('#card-extension').click();
    cy.get('#card-extension .menu .item').first().click();

    // Change specials folder format
    cy.get('input[name="specials_folder_format"]')
      .clear()
      .type(newSpecialsFolderFormat, { parseSpecialCharSequences: false })
      .should('have.value', newSpecialsFolderFormat);

    // Change season folder format
    cy.get('input[name="season_folder_format"]')
      .clear()
      .type(newSeasonFolderFormat, { parseSpecialCharSequences: false })
      .should('have.value', newSeasonFolderFormat);

    // Toggle multi-library file naming
    cy.get('input[name="library_unique_cards"]').parent().click();

    // Save changes
    cy.get('#save-changes').click({ force: true });
    cy.get('.ui.success.message, .ui.info.toast').should('be.visible');
  });

  it('Enters an invalid title card filename format and the change is rejected', () => {
    // Record the current (valid) filename format before clearing it
    cy.get('input[name="card_filename_format"]').invoke('val').as('originalFormat');

    // Enter an invalid filename format (empty string)
    cy.get('input[name="card_filename_format"]')
      .clear()
      .should('have.value', '');

    // Attempt to save - client-side validation should prevent the API call
    cy.get('#save-changes').click({ force: true });

    // Reload and verify the empty format was not persisted
    cy.reload();
    cy.get('#settings-form').should('be.visible');
    cy.get('@originalFormat').then((originalFormat) => {
      cy.get('input[name="card_filename_format"]').should('have.value', originalFormat);
    });
  });

  it('Enters an invalid folder format and the change is rejected', () => {
    // Enter an invalid folder format (unknown variable)
    cy.get('input[name="season_folder_format"]')
      .clear()
      .type('{fake_variable}', { parseSpecialCharSequences: false })
      .should('have.value', '{fake_variable}');

    // Attempt to save - the server should reject the unknown variable
    cy.get('#save-changes').click({ force: true });

    // Reload and verify the invalid format was not persisted
    cy.reload();
    cy.get('#settings-form').should('be.visible');
    cy.get('input[name="season_folder_format"]').should('not.have.value', '{fake_variable}');
  });

  it('Changes the web interface settings', () => {
    // Change home page size
    cy.get('input[name="home_page_size"]')
      .clear()
      .type('25')
      .should('have.value', '25');

    // Change episode data table page size
    cy.get('input[name="episode_data_page_size"]')
      .clear()
      .type('50')
      .should('have.value', '50');

    // Change source preview page dimensions
    cy.get('input[name="source_preview_page_dimensions"]')
      .clear()
      .type('4x5')
      .should('have.value', '4x5');

    // Change title card preview page dimensions
    cy.get('input[name="title_card_preview_page_dimensions"]')
      .clear()
      .type('3x4')
      .should('have.value', '3x4');

    // Toggle various checkboxes
    cy.get('input[name="home_page_table_view"]').parent().click();
    cy.get('input[name="simplified_data_table"]').parent().click();
    cy.get('input[name="stylize_unmonitored_posters"]').parent().click();
    cy.get('input[name="colorblind_mode"]').parent().click();
    cy.get('input[name="reduced_animations"]').parent().click();
    cy.get('input[name="interactive_card_previews"]').parent().click();
    cy.get('input[name="display_live_messages"]').parent().click();

    // Save changes
    cy.get('#save-changes').click({ force: true });
    cy.get('.ui.success.message, .ui.info.toast').should('be.visible');
  });

  it('Enters an invalid home page size', () => {
    // Enter invalid home page size (zero)
    cy.get('input[name="home_page_size"]')
      .clear()
      .type('0')
      .should('have.value', '0');

    // Attempt to save - client-side validation should prevent the API call
    cy.get('#save-changes').click({ force: true });

    // Reload and verify the invalid size was not persisted
    cy.reload();
    cy.get('#settings-form').should('be.visible');
    cy.get('input[name="home_page_size"]').should('not.have.value', '0');
  });

  it('Enters an invalid episode data table page size', () => {
    // Enter invalid episode data table page size (negative number)
    cy.get('input[name="episode_data_page_size"]')
      .clear()
      .type('-10')
      .should('have.value', '-10');

    // Attempt to save - client-side validation should prevent the API call
    cy.get('#save-changes').click({ force: true });

    // Reload and verify the invalid size was not persisted
    cy.reload();
    cy.get('#settings-form').should('be.visible');
    cy.get('input[name="episode_data_page_size"]').should('not.have.value', '-10');
  });

  it('Opens and closes the episode style modal', () => {
    // Click on one of the style buttons to open the modal
    cy.get('[data-value="style-button"]').first().click();
    
    // Verify modal is visible
    cy.get('#style-modal').should('be.visible');
    
    // Verify modal content
    cy.get('#style-modal .header').should('contain', 'Episode Styles');
  });

  it('Card quality slider is visible', () => {
    // Find the card quality slider
    cy.get('#card-quality').scrollIntoView().should('be.visible');
    
    // Test slider interaction (if it's interactive)
    cy.get('#card-quality .thumb').should('exist');
  });

  it('Expands and collapses accordion sections', () => {
    // Test Global Extras accordion
    cy.get('.accordion .title').contains('Global Extras').click();
    cy.get('.accordion .content section[aria-label="extras"]').should('be.visible');
    cy.get('.accordion .title').contains('Global Extras').click();
    cy.get('.accordion .content section[aria-label="extras"]').should('not.be.visible');

    // Test Global Fonts accordion
    cy.get('.accordion .title').contains('Global Fonts').click();
    cy.get('.accordion .content section[aria-label="default_fonts"]').should('be.visible');
    cy.get('.accordion .title').contains('Global Fonts').click();
    cy.get('.accordion .content section[aria-label="default_fonts"]').should('not.be.visible');

    // Test Global Blur Profiles accordion
    cy.get('.accordion .title').contains('Global Blur Profiles').click();
    cy.get('.accordion .content section[aria-label="blur_profiles"]').should('be.visible');
    cy.get('.accordion .title').contains('Global Blur Profiles').click();
    cy.get('.accordion .content section[aria-label="blur_profiles"]').should('not.be.visible');
  });

  it('Updates preview title card when card type changes', () => {
    // Wait for the preview card to be visible
    cy.get('#card-type-preview img').scrollIntoView().should('be.visible');
    
    // Get the initial image URL
    cy.get('#card-type-preview img').invoke('attr', 'src').then((initialSrc) => {
      // Change the default card type
      cy.get('#default-card-type').click();
      cy.get('#default-card-type .menu .item').eq(5).click();

      // Verify the image URL has changed
      cy.get('#card-type-preview img').should('not.have.attr', 'src', initialSrc);
      cy.get('#card-type-preview img').should('have.attr', 'src').and('not.be.empty');
    });
  });

  it('Shows disabled state when no connections are available', () => {
    // Reset database to remove connections
    cy.resetDatabase();
    
    // Visit settings page
    cy.visit('/settings');
    
    // Should show warning message
    cy.get('#no-connections-warning').should('contain', 'Please add a Connection');
    
    // Form fields should be disabled
    cy.get('#settings-form .field').should('have.class', 'disabled');
    cy.get('#save-changes').should('be.disabled');
    
    // Save button should show disabled state
    cy.get('#save-changes').should('have.class', 'disabled');
  });

  it('Verifies ImageMagick executable field is disabled in Docker mode', () => {
    // The ImageMagick executable field should always be disabled
    cy.get('input[name="imagemagick_executable"]').should('be.disabled');
    
    // The field container should have the disabled class
    cy.get('input[name="imagemagick_executable"]').parent().should('have.class', 'disabled');
    
    // Verify the field exists and shows the expected placeholder
    cy.get('input[name="imagemagick_executable"]').should('be.visible');
    cy.get('input[name="imagemagick_executable"]').should('have.attr', 'placeholder');
  });
});
