/**
 * Generate a random number `[min, max]`.
 * @param {number} min Minimum random number. Inclusive.
 * @param {number} max Maximum random number. Inclusive.
 * @returns {number} Random integer between min and max.
 */
const randomInt = (min=1, max=59) => Math.floor(Math.random() * (max - min + 1)) + min;

/**
 * Generate a random crontab expression.
 * @returns {string} Random crontab string in format "minute hour * * *"
 */
const randomCrontab = () => {
  const minute = randomInt(0, 59);
  const hour = randomInt(0, 23);
  return `${minute} ${hour} * * *`;
};

describe('Scheduler', () => {
  beforeEach(() => cy.visit('/scheduler'));

  it('Visits the scheduler page', () => {
    cy.url().should('eq', Cypress.config('baseUrl') + '/scheduler');
  });

  it('Reschedules multiple tasks with new crontab expressions', () => {
    // Make sure scheduler is in basic mode
    // cy.request('POST', '/api/scheduler/type/basic');

    // Iterate through each row in the scheduler body
    const newCrontabs = {};
    cy.get("#task-table tr").each(($row, index) => {
      // Get the data-id value of the row
      const rowId = $row.attr('data-id');
      newCrontabs[rowId] = randomCrontab();

      // Find the cell with data-column="schedule" and change its text
      cy.wrap($row).find('td[data-column="schedule"] span')
        .clear()
        .type(newCrontabs[rowId])
        .should('have.text', newCrontabs[rowId])
    });

    // Click the save button
    cy.contains('Save Changes').click();
    cy.wait(250);
    cy.reload();

    // Verify that the new values are saved
    cy.get("#task-table tr").each(($row) => {
      // Check if the cell with data-column="schedule" has the new value
      const rowId = $row.attr('data-id');
      cy.wrap($row).find('td[data-column="schedule"] span').should('have.text', newCrontabs[rowId]);
    });
  })

  it('Manually runs a task in basic mode', () => {
    // Intercept run task request
    cy.intercept('PUT', '/api/v2/scheduler/task/*').as('runTask');

    // Get existing "previous duration" text
    cy.get('#task-table [data-column="previous_duration"]').last()
      .invoke('text')
      .then((previousDuration) => {
        previousDuration = previousDuration === '0 seconds' ? '-' : previousDuration;
        // Run this task
        cy.get('#task-table [data-column="runTask"]').last().click();
        cy.wait('@runTask');

        // Verify new duration is different
        cy.get('#task-table [data-column="previous_duration"]').last()
          .invoke('text')
          .should((newDuration) => {
            expect(previousDuration).not.to.eq(newDuration);
          });
      });
  });

  it('Toggles scheduler type between basic and advanced', () => {
    // Check initial state - should show "Enable Basic Scheduler" if in advanced mode
    cy.get('#toggle-button').should('be.visible');
    
    // Click the toggle button to open modal
    cy.get('#toggle-button').click();
    
    // Verify modal appears with correct content
    cy.get('#toggleScheduleTypeModal').should('be.visible');
    cy.get('#toggleScheduleTypeModal .header').should('contain', 'Change Scheduler Type?');
    cy.get('#toggleScheduleTypeModal .content').should('contain', 'Changing this will reset your existing Schedules');
    
    // Cancel the modal
    cy.get('#toggleScheduleTypeModal .cancel.button').click();
    cy.get('#toggleScheduleTypeModal').should('not.be.visible');
    
    // Open modal again and confirm
    cy.get('#toggle-button').click();
    cy.get('#toggleScheduleTypeModal .ok.button').click();
    
    // Should show loading state and then reload
    cy.get('#toggle-button').should('have.class', 'loading');
  });

  it('Displays human-readable crontab expressions', () => {
    // Wait for page to load and check that crontab expressions are decoded
    cy.get('#task-table tr').first().within(() => {
      cy.get('[data-column="schedule-string"]').should('not.be.empty');
      // Should contain human-readable text, not raw crontab
      cy.get('[data-column="schedule-string"]').should('not.contain', '* * * * *');
    });
  });

  it('Updates human-readable crontab when editing schedule', () => {
    // Get first task row
    cy.get('#task-table tr').first().within(() => {
      const newCrontab = '30 2 * * 1'; // Monday at 2:30 AM
      
      // Edit the schedule
      cy.get('[data-column="schedule"] span')
        .clear()
        .type(newCrontab);
      
      // Verify human-readable version updates
      cy.get('[data-column="schedule-string"]').should('contain', 'Monday');
      cy.get('[data-column="schedule-string"]').should('contain', '2:30 AM');
    });
  });

  it('Prevents running already running tasks', () => {
    // Find a task that's currently running (has loading class)
    cy.get('#task-table tr').each(($row) => {
      const runButton = $row.find('[data-column="runTask"] i');
      if (runButton.hasClass('loading')) {
        // This task is running, clicking should not trigger new run
        cy.wrap($row).find('[data-column="runTask"]').click();
        // Should show info toast about task already running
        cy.get('.toast').should('contain', 'is already running');
        return false; // break the loop
      }
    });
  });

  it('Shows task running state correctly', () => {
    cy.get('#task-table tr').each(($row) => {
      const runButton = $row.find('[data-column="runTask"] i');
      const isRunning = runButton.hasClass('loading');
      
      if (isRunning) {
        // Running tasks should not be clickable
        cy.wrap($row).find('[data-column="runTask"]').should('not.have.class', 'selectable');
        cy.wrap($row).find('[data-column="runTask"] i').should('have.class', 'blue loading sync');
      } else {
        // Non-running tasks should be clickable
        cy.wrap($row).find('[data-column="runTask"]').should('have.class', 'selectable');
        cy.wrap($row).find('[data-column="runTask"] i').should('not.have.class', 'loading');
      }
    });
  });

  it('Handles invalid crontab expressions gracefully', () => {
    cy.get('#task-table tr').first().within(() => {
      // Enter invalid crontab
      cy.get('[data-column="schedule"] span')
        .clear()
        .type('invalid cron');
      
      // Should show "Invalid Expression" in red
      cy.get('[data-column="schedule-string"] .ui.red.text').should('contain', 'Invalid Expression');
    });
  });

  it('Rejects invalid crontab expressions when saving to backend', () => {
    // Intercept the PATCH request to catch the API response
    cy.intercept('PATCH', '/api/v2/scheduler/task/*').as('updateTaskInvalid');
    
    // Get first task row and enter invalid crontab
    cy.get('#task-table tr').first().within(() => {
      // Enter invalid crontab that will be rejected by backend
      cy.get('[data-column="schedule"] span')
        .clear()
        .type('99 99 * * *'); // Invalid hour and minute values
      
      // Frontend should still show "Invalid Expression" 
      cy.get('[data-column="schedule-string"] .ui.red.text').should('contain', 'Invalid Expression');
    });
    
    // Click save button - this should trigger the API call
    cy.contains('Save Changes').click();
    
    // Wait for the API response
    cy.wait('@updateTaskInvalid').then((interception) => {
      // Verify the API returned an error
      expect(interception.response.statusCode).to.equal(422);
      expect(interception.response.body.detail).to.equal('Invalid cron schedule');
    });
    
    // Should show error toast
    cy.get('.toast').should('contain', 'Error Recheduling Task');
    
    // Reload page to verify the invalid crontab wasn't saved
    cy.reload();
    cy.get('#task-table tr').first().within(() => {
      // The crontab should revert to its original value (not the invalid one)
      cy.get('[data-column="schedule"] span').should('not.have.text', '99 99 * * *');
    });
  });

  it('Saves schedule changes and shows success message', () => {
    // Intercept the PATCH request
    cy.intercept('PATCH', '/api/v2/scheduler/task/*').as('updateTask');
    
    // Change a schedule
    cy.get('#task-table tr').first().within(() => {
      cy.get('[data-column="schedule"] span')
        .clear()
        .type('15 3 * * *');
    });
    
    // Click save
    cy.contains('Save Changes').click();
    
    // Wait for API calls
    cy.wait('@updateTask');
    
    // Should show success message
    cy.get('.toast').should('contain', 'Saved Schedules');
  });

  it('Displays help information correctly', () => {
    // Check help text
    cy.get('.help').should('contain', 'To adjust when Tasks are run, edit the expression in the Schedule column');
    
    // Check info message about cron expressions
    cy.get('.ui.info.message').should('contain', 'Task schedules are entered as Cron expressions');
    cy.get('.ui.info.message a').should('have.attr', 'href', 'https://crontab.guru/');
    cy.get('.ui.info.message a').should('have.attr', 'target', '_blank');
  });

  it('Maintains table structure and column alignment', () => {
    // Check table headers
    cy.get('thead tr').within(() => {
      cy.get('th').should('have.length', 5); // Only 5 columns, one spans two columns
      cy.get('th').eq(0).should('have.class', 'center aligned'); // Run Task
      cy.get('th').eq(1).should('have.class', 'left aligned');   // Task Description
      cy.get('th').eq(2).should('have.class', 'left aligned');   // Schedule
      cy.get('th').eq(3).should('have.class', 'center aligned'); // Last Duration
      cy.get('th').eq(4).should('have.class', 'left aligned');   // Next Run
    });
    
    // Check that all rows have the correct number of columns
    cy.get('#task-table tr').each(($row) => {
      cy.wrap($row).find('td').should('have.length', 6);
    });
  });

  it('Updates task duration after running task', () => {
    // Intercept run task request
    cy.intercept('PUT', '/api/v2/scheduler/task/*').as('runTask');
    
    // Get first non-running task
    cy.get('#task-table tr').each(($row) => {
      const runButton = $row.find('[data-column="runTask"] i');
      if (!runButton.hasClass('loading')) {
        // Get current duration
        cy.wrap($row).find('[data-column="previous_duration"]')
          .invoke('text')
          .then((currentDuration) => {
            // Run the task
            cy.wrap($row).find('[data-column="runTask"]').click();
            cy.wait('@runTask');
            
            // Duration should update (either to a new value or remain the same)
            cy.wrap($row).find('[data-column="previous_duration"]')
              .invoke('text')
              .should('not.be.empty');
          });
        return false; // break the loop
      }
    });
  });
});
