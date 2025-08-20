describe('Fonts Page', () => {
  beforeEach(() => {
    // Reset database and create test connections
    cy.resetDatabase();
    cy.createObjectAndGetId('/api/v2/fonts/font/new', {
      'name': 'Test Font',
    });

    // Create some test templates and libraries
    cy.createObjectAndGetId('/api/v2/templates/template/new', {
      'name': 'Test Template 1',
      'card_type': 'standard'
    });

    cy.createObjectAndGetId('/api/v2/templates/template/new', {
      'name': 'Test Template 2', 
      'card_type': 'anime'
    });

    // Visit the fonts page
    cy.visit('/fonts');
  });

  describe('Page Structure and Navigation', () => {
    it('should display the correct page title and sections', () => {
      cy.get('h1').should('contain', 'Fonts');
      cy.get('#create-font').should('be.visible').click();
      cy.get('#fonts').should('be.visible');
    });

    it('should show help information about fonts', () => {
      cy.get('.ui.info.message').should('be.visible');
      cy.get('.ui.info.message .header').should('contain', 'What are Fonts?');
    });

    it('should have create new font button', () => {
      cy.get('#create-font').should('be.visible');
      cy.get('#create-font').should('contain', 'Create New Font');
    });
  });

  describe('Font Creation and Management', () => {
    it('should create a new blank font when create button is clicked', () => {
      cy.get('#create-font').click();

      // Wait for font to be created and page to reload
      cy.get('#fonts .ui.accordion').should('be.visible');

      // Should have one font accordion
      cy.get('#fonts .ui.accordion').should('have.length', 1);

      // Should show success message
      cy.get('.toast').should('contain', 'Created Font');
    });

    it('should display font accordion with correct structure', () => {
      cy.get('#fonts .ui.accordion').should('be.visible');
      cy.get('#fonts .ui.accordion').first().find('.title').should('contain', 'Test Font');
    });

    it('should expand font accordion when title is clicked', () => {
      const fontAccordion = cy.get('#fonts .ui.accordion').first();
      cy.get('#fonts .ui.accordion').first().within(() => {
        // Initially should be collapsed
        cy.get('.content').should('not.have.class', 'active');

        // Click to expand
        cy.get('.title').click();

        // Should now be expanded
        cy.get('.content').should('have.class', 'active');
      });
    });
  });

  describe('Font Form Fields', () => {
    beforeEach(() => {
      cy.get('#fonts .ui.accordion').first().find('.title').click();
    });

    it('should have all required form fields', () => {
      cy.get('#fonts .ui.accordion').first().within(() => {
        // Basic fields
        cy.get('input[name="name"]').should('be.visible');
        cy.get('input[name="name"]').should('have.attr', 'placeholder', 'Font Name');
        cy.get('input[name="name"]').should('have.attr', 'minlength', '1');
  
        // File upload
        cy.get('input[name="font_file"]').should('be.visible');
        cy.get('input[name="font_file"]').should('have.attr', 'accept', '.otf,.ttf,.ttc,.font/*');
  
        // Color field
        cy.get('input[name="color"]').should('be.visible');
        cy.get('input[name="color"]').should('have.attr', 'placeholder', 'Default');
        cy.get('.inline.color.circle').should('be.visible');
        cy.get('a[href*="imagemagick.org"]').should('be.visible');
  
        // Text case dropdown
        cy.get('[data-value="title_case"]').should('be.visible');
        cy.get('[data-value="title_case"] .default.text').should('contain', 'Default');
  
        // Title split modifier
        cy.get('input[name="line_split_modifier"]').should('be.visible');
        cy.get('input[name="line_split_modifier"]').should('have.attr', 'placeholder', '0');

        // Size field with percentage label
        cy.get('input[name="size"]').should('be.visible');
        cy.get('input[name="size"]').should('have.attr', 'placeholder', '100');
        cy.get('input[name="size"]').parent().find('.ui.basic.label').should('contain', '%');

        // Kerning field with percentage label
        cy.get('input[name="kerning"]').should('be.visible');
        cy.get('input[name="kerning"]').should('have.attr', 'placeholder', '100');
        cy.get('input[name="kerning"]').parent().find('.ui.basic.label').should('contain', '%');

        // Stroke width field with percentage label
        cy.get('input[name="stroke_width"]').should('be.visible');
        cy.get('input[name="stroke_width"]').should('have.attr', 'placeholder', '100');
        cy.get('input[name="stroke_width"]').parent().find('.ui.basic.label').should('contain', '%');

        // Interline spacing
        cy.get('input[name="interline_spacing"]').should('be.visible');
        cy.get('input[name="interline_spacing"]').should('have.attr', 'placeholder', '0');

        // Interword spacing
        cy.get('input[name="interword_spacing"]').should('be.visible');
        cy.get('input[name="interword_spacing"]').should('have.attr', 'placeholder', '0');

        // Vertical shift
        cy.get('input[name="vertical_shift"]').should('be.visible');
        cy.get('input[name="vertical_shift"]').should('have.attr', 'placeholder', '0');
      });
    });

    it('should have character replacement fields and buttons', () => {
      cy.get('#fonts .ui.accordion').first().within(() => {
        // Character replacements section
        cy.get('label').contains('Character Replacements').should('be.visible');
        
        // Analyze button
        cy.get('[data-action="populateReplacements"]').should('be.visible');
        cy.get('[data-action="populateReplacements"]').should('contain', 'Analyze Font Replacements');
        cy.get('[data-action="populateReplacements"] .magic.icon').should('be.visible');
        
        // Add replacement button
        cy.get('[data-action="addReplacement"]').should('be.visible');
        cy.get('[data-action="addReplacement"]').should('contain', 'Add Replacement');
        cy.get('[data-action="addReplacement"] .plus.square.outline.icon').should('be.visible');
      });
    });

    it('should have action buttons', () => {
      cy.get('#fonts .ui.accordion').first().within(() => {
        // Save button
        cy.get('button[data-action="save"]').should('be.visible');
        cy.get('button[data-action="save"]').should('contain', 'Save');
        cy.get('button[data-action="save"]').should('have.class', 'primary');
        cy.get('button[data-action="save"] .save.icon').should('be.visible');
  
        // Transfer button
        cy.get('button[data-action="transfer"]').should('be.visible');
        cy.get('button[data-action="transfer"]').should('contain', 'Transfer');
        cy.get('button[data-action="transfer"]').should('have.class', 'teal');
        cy.get('button[data-action="transfer"] .file.import.icon').should('be.visible');
  
        // Delete button
        cy.get('button[data-action="delete"]').should('be.visible');
        cy.get('button[data-action="delete"]').should('contain', 'Delete');
        cy.get('button[data-action="delete"]').should('have.class', 'negative');
        cy.get('button[data-action="delete"] .trash.icon').should('be.visible');
      });
      
    });
  });

  describe('Text Case Dropdown Options', () => {
    beforeEach(() => {
      cy.get('#fonts .ui.accordion').first().find('.title').click();
    });

    it('should show all text case options when dropdown is clicked', () => {
      cy.get('#fonts .ui.accordion').first().within(() => {
        cy.get('[data-value="title_case"]').click();
        cy.get('[data-value="title_case"] .menu').should('be.visible');
  
        // Check all options are present
        cy.get('[data-value="title_case"] .menu .item').should('contain', 'Blank');
        cy.get('[data-value="title_case"] .menu .item').should('contain', 'Lowercase');
        cy.get('[data-value="title_case"] .menu .item').should('contain', 'Source');
        cy.get('[data-value="title_case"] .menu .item').should('contain', 'Title');
        cy.get('[data-value="title_case"] .menu .item').should('contain', 'Uppercase');
      });
    });

    it('should select text case option when clicked', () => {
      cy.get('#fonts .ui.accordion').first().within(() => {
        cy.get('[data-value="title_case"]').click();
        cy.get('[data-value="title_case"] .menu .item').contains('Title').click();
        cy.get('[data-value="title_case"] .text').should('contain', 'Title');
      });
    });
  });

  describe('Preview Section', () => {
    beforeEach(() => {
      cy.get('#create-font').click();
      cy.get('#fonts .ui.accordion').first().find('.title').click();
    });

    it('should have preview controls in the right column', () => {
      cy.get('#fonts .ui.accordion').first().find('[data-label="preview-form"]').within(() => {
        // Refresh button
        cy.get('button[data-action="refresh"]').should('be.visible');
        cy.get('button[data-action="refresh"]').should('contain', 'Refresh Preview');
  
        // Preview form
        cy.get('[data-value="preview-form"]').should('be.visible');
      });
    });

    it('should have preview form fields', () => {
      cy.get('#fonts .ui.accordion').first().find('[data-label="preview-form"]').within(() => {
        // Card type dropdown
        cy.get('.dropdown[data-value="card_type"]').should('be.visible');

        // Title text input
        cy.get('input[name="title_text"]').should('be.visible');
        cy.get('input[name="title_text"]').should('have.value', 'Example Title');
      });
    });

    it('should have blank preview image card', () => {
      cy.get('#fonts .ui.accordion').first().find('[data-label="preview-form"]').within(() => {
        cy.get('.ui.fluid.raised.card').should('be.visible');
        cy.get('.ui.fluid.raised.card .content img').should('be.visible');
        cy.get('.ui.fluid.raised.card .content img').should('have.attr', 'src', '/public/blank.png');
      });
    });

    it('should show info message about custom font files', () => {
      cy.get('#fonts .ui.accordion [data-label="preview-form"] .ui.info.message').first().should('be.visible');
    });
  });

  describe('Font Operations', () => {
    beforeEach(() => {
      cy.get('#fonts .ui.accordion').first().find('.title').click();
    });

    it('should save font when save button is clicked', () => {
      cy.get('#fonts .ui.accordion').first().find('form[data-label="font-form"]').within(() => {
        // Fill in some form data
        cy.get('input[name="name"]').clear().type('Test Font');
        cy.get('input[name="color"]').type('red');
        cy.get('input[name="size"]').clear().type('120');
  
        // Intercept save request
        cy.intercept('PATCH', '/api/v2/fonts/font/*').as('updateFont');

        // Click save
        cy.get('button[data-action="save"]').click();
      });

      // Wait for save to complete
      cy.wait('@updateFont').then((interception) => {
        const response = interception.response;
        expect(response.statusCode).to.eq(200);
        expect(response.body.name).to.eq('Test Font');
        expect(response.body.color).to.eq('red');
        expect(response.body.size).to.eq(1.2);
      });
    });

    it('should delete font when delete button is clicked', () => {
      cy.get('#fonts .ui.accordion').first().find('form[data-label="font-form"]').within(() => {
        // Intercept delete request
        cy.intercept('DELETE', '/api/v2/fonts/font/*').as('deleteFont');

        // Click delete
        cy.get('button[data-action="delete"]').click();
      });

      cy.wait('@deleteFont').then((interception) => {
        const response = interception.response;
        expect(response.statusCode).to.be.oneOf([200, 204]);
      });

      // Font should be removed from page
      cy.get('#fonts .ui.accordion').should('have.length', 0);
    });

    it('should show transfer modal when transfer button is clicked', () => {
      // Create another Font
      cy.get('#create-font').click();
      cy.reload();
      cy.get('#fonts .ui.accordion .title').contains('Test Font').click();

      // Click transfer button
      cy.get('#fonts .ui.accordion .active.content').find('[data-label="font-form"] button[data-action="transfer"]').click();
      cy.get('#fonts .ui.accordion .active.content').find('[data-label="font-form"] button[data-action="transfer"] .menu .item').contains('Blank Custom Font').click();

      // Modal should be visible
      cy.get('#transfer-font-modal').should('be.visible');
      cy.get('#transfer-font-modal .header').should('contain', 'Transfer all references of this Font?');

      // Modal should have correct buttons
      cy.get('#transfer-font-modal [data-action="cancel-transfer"]').should('be.visible');
      cy.get('#transfer-font-modal [data-action="cancel-transfer"]').should('contain', 'No');

      cy.get('#transfer-font-modal [data-action="transfer-only"]').should('be.visible');
      cy.get('#transfer-font-modal [data-action="transfer-only"]').should('contain', 'Yes');

      cy.get('#transfer-font-modal [data-action="transfer-with-delete"]').should('be.visible');
      cy.get('#transfer-font-modal [data-action="transfer-with-delete"]').should('contain', 'Yes, and delete this Font afterwards');
    });
  });

  describe('Transfer Modal Functionality', () => {
    beforeEach(() => {
      cy.get('#fonts .ui.accordion').first().find('.title').click();
      cy.get('#create-font').click();
      cy.reload();
      cy.get('#fonts .ui.accordion .title').contains('Test Font').click();

      // Click transfer button
      cy.get('#fonts .ui.accordion .active.content').find('[data-label="font-form"] button[data-action="transfer"]').click();
      cy.get('#fonts .ui.accordion .active.content').find('[data-label="font-form"] button[data-action="transfer"] .menu .item').contains('Blank Custom Font').click();
    });

    it('should close modal when cancel button is clicked', () => {
      cy.get('#transfer-font-modal [data-action="cancel-transfer"]').click();
      cy.get('#transfer-font-modal').should('not.be.visible');
    });

    it('should close modal when transfer only button is clicked', () => {
      cy.get('#transfer-font-modal [data-action="transfer-only"]').click();
      cy.get('#transfer-font-modal').should('not.be.visible');
    });

    it('should close modal when transfer with delete button is clicked', () => {
      cy.get('#transfer-font-modal [data-action="transfer-with-delete"]').click();
      cy.get('#transfer-font-modal').should('not.be.visible');
    });
  });

  describe('Multiple Fonts Management', () => {
    it('should handle multiple fonts correctly', () => {
      // Remove all fonts
      cy.resetDatabase();
      cy.reload();

      // Create first font
      cy.get('#create-font').click();
      cy.get('#fonts .ui.accordion').should('have.length', 1);

      // Create second font
      cy.get('#create-font').click();
      cy.get('#fonts .ui.accordion').should('have.length', 2);

      // Create third font
      cy.get('#create-font').click();
      cy.get('#fonts .ui.accordion').should('have.length', 3);
    });
  });

  describe('Font File Upload', () => {
    beforeEach(() => {
      cy.get('#create-font').click();
      cy.get('#fonts .ui.accordion').first().find('.title').click();
    });

    it('should accept font file uploads', () => {
      cy.get('#fonts .ui.accordion').first().find('form[data-label="font-form"]').within(() => {
        // Check file input accepts correct formats
        cy.get('input[name="font_file"]').should('have.attr', 'accept', '.otf,.ttf,.ttc,.font/*');

        // File input should be visible and enabled
        cy.get('input[name="font_file"]').should('be.visible');
        cy.get('input[name="font_file"]').should('not.be.disabled');
      });
    });
  });

  describe('Responsive Design', () => {
    it('should display correctly on different screen sizes', () => {
      // Test mobile viewport
      cy.viewport('iphone-x');
      cy.get('#fonts').should('be.visible');
      cy.get('#create-font').should('be.visible');

      // Test tablet viewport
      cy.viewport('ipad-2');
      cy.get('#fonts').should('be.visible');
      cy.get('#create-font').should('be.visible');

      // Test desktop viewport
      cy.viewport('macbook-15');
      cy.get('#fonts').should('be.visible');
      cy.get('#create-font').should('be.visible');
    });
  });
});
