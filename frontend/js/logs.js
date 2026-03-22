{% if False %}
import {
  LogEntry,
  LogInternalServerError,
  LogLevel,
  Page,
} from './.types.js';
{% endif %}

/**
 * Parse a Date from the given file name.
 * @param {string} name - Name to extract the Date from.
 * @returns {Date} parsed from the given name.
 */
function parseDate(name) {
  const pattern = /(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})/;
  try {
    const [, datePart, timePart] = name.match(pattern);
    const [year, month, day] = datePart.split("-");
    const [hour, minute, second] = timePart.split("-");
    return new Date(year, month - 1, day, hour, minute, second);
  } catch {
    return new Date();
  }
}

/**
 * Set the given level as the currently selected value in the dropdown.
 * @param {LogLevel} level - The level to set as the current selection in the
 * dropdown.
 */
function updateMessageLevel(level) {
  const newLevel = level.toUpperCase();
  $('.dropdown[data-value="level"]').dropdown('set text', newLevel);
  $('.dropdown[data-value="level"]').dropdown('set selected', newLevel);
  $('.dropdown[data-value="level"]').dropdown('set value', newLevel);
}

/**
 * Set the timestamp filter field to the given value. This updates the "after"
 * field if blank, then the before field. If neither are blank nothing happens.
 * @param {string} timestamp - Timestamp to set as the current value.
 */
function updateTimestamp(timestamp) {
  // Get current values of before/after
  const currentAfter = document.querySelector('input[name="after"]').value;
  const currentBefore = document.querySelector('input[name="before"]').value;

  // Populate after if blank, else before
  if (currentAfter === '') {
    document.querySelector('input[name="after"]').value = timestamp;
  } else if (currentBefore === '') {
    document.querySelector('input[name="before"]').value = timestamp;
  }
}

/**
 * Add the given context ID to the current log filter input field.
 * @param {string} id - Unique context ID to add to the current log filters.
 */
function appendContextID(id) {
  // Get current value
  const currentVal = document.querySelector('input[name="context_id"]').value;
  // Only append if ID is not already listed
  if (!currentVal.includes(id)) {
    document.querySelector('input[name="context_id"]').value = currentVal === '' ? id : `${currentVal},${id}`;
  }
}

/** Reset the filter form. */
const resetForm = () => $('#log-filters').form('clear');

/**
 * Parse the given message into navigation links around "objects" like Series,
 * Templates, Syncs, etc. Also stylizes redacted messages.
 * @param {string} message Message to parse for links to objects.
 * @param {string} searchText Text was used to filter log messages with. Used in
 * text highlighting.
 * @returns {string} Modified message.
 */
function addRichFormatting(message, searchText='') {
  // Apply search text highlighting first
  searchText.split('|').forEach(subString => {
    message = message.replace(
      subString,
      `<span class="ui yellow text">${subString}</span>`,
    )
  });

  // Apply rich formatting to the message
  message = message
    .replace(
      /Series\[(\d+)\]/g,
      (match, seriesID) => `<a href="/series/${seriesID}">${match}</a>`
    ).replace(
      /Task\[\w+\]/g,
      (match) => `<a href="/scheduler">${match}</a>`
    ).replace(
      /Sync\[\d+\]/g,
      (match) => `<a href="/sync">${match}</a>`
    ).replace(
      /(Emby|Jellyfin|Plex|Sonarr|TMDb|TVDb)(Connection|Interface)\[\d+\]/g,
      (match) => `<a href="/connections">${match}</a>`
    ).replace(
      /Template\[\d+\]/g,
      (match) => `<a href="/card-templates">${match}</a>`
    ).replace(
      /Font\[(\d+)\]/g,
      (match, fontID) => `<a href="/fonts#font-id${fontID}">${match}</a>`
    ).replace(
      /\[REDACTED\]/g,
      () => `<span class="redacted text">[REDACTED]</span>`,      
    ).replace(
      /(Finished in \d+\.\d+ms) \(((\d)\d\d .+)\)/g,
      (match, durationText, statusText, statusCode) => {
        const color = {1: 'grey', 2: 'green', 3: 'olive', 4: 'orange', 5: 'red'}[statusCode]
        return `${durationText} (<span class="ui ${color} text">${statusText}</span>)`;
      }
    )
  ;
    
  return message;
}

/**
 * Submit an API request to query for the given page of logs. If successful,
 * then add those logs to the DOM.
 * @param {number} [page=1] - Page number of logs to query.
 */
function queryForLogs(page=1) {
  // Mark icon as loadin
  const $icon = setLoadingIcon($('[data-action="refresh"] .icon'));

  // Prepare Form
  const form = new FormData(document.getElementById('log-filters'));

  // Remove blank values
  for (let [key, value] of [...form.entries()]) {
    if (value === '') { form.delete(key); }
  }

  // Create query param string
  const queryString = [...form.entries()]
    .map(x => `${encodeURIComponent(x[0])}=${encodeURIComponent(x[1])}`)
    .join('&')
  ;

  // Submit API request
  $.ajax({
    type: 'GET',
    url: `/api/v2/logs/query?page=${page}&${queryString}`,
    /**
     * Logs queries successfully, add rows for each log message to the DOM.
     * @param {Page<LogEntry>} messages Log messages to update the table with.
     */
    success: messages => {
      const rows = messages.items.map(message => {
        // Clone template
        const row = document.querySelector(`#${message.level_name.toLowerCase()}-message-template`).content.cloneNode(true);

        const shortTime = message.timestamp.match(/^(.[^\.]+\.\d{3}?)\d*$/m);
        if (shortTime) {
          row.querySelector('[data-value="timestamp"]').innerText = shortTime[1];
        } else {
          row.querySelector('[data-value="timestamp"]').innerText = message.timestamp;
        }
        row.querySelector('[data-value="context_id"]').innerText = message.context_id
          ? message.context_id
          : ''
        ;

        if (message.context_id) {
          row.querySelector('[data-value="context_id"]').innerText = message.context_id;
        } else {
          row.querySelector('[data-value="context_id"]').innerText = '';
          delete row.querySelector('[data-value="context_id"]').dataset.tooltip;
          row.querySelector('[data-value="context_id"]').classList.remove('selectable');
        }

        if (message.exception_traceback) {
          row.querySelector('[data-value="message"]').classList.add('code');
          row.querySelector('[data-value="message"]').innerText = message.message + '\n\n' + message.exception_traceback;
        } else if (
          message.message.startsWith('Internal Server Error')
          || message.message.includes('─ ImageMagick Command ─')
          || message.message.includes('Traceback (most recent call last)')
        ) {
          row.querySelector('[data-value="message"]').classList.add('code');
          row.querySelector('[data-value="message"]').innerText = message.message;
        } else {
          row.querySelector('[data-value="message"]').innerHTML = addRichFormatting(
            message.message,
            document.querySelector('input[name="contains"]').value,
          );
        }

        // On click of log level, update filter level
        row.querySelector('[data-value="level_name"]').onclick = () => updateMessageLevel(message.level_name);
        
        // On click of timestamp, update before/after fields
        row.querySelector('[data-value="timestamp"]').onclick = () => updateTimestamp(message.timestamp);
        
        // On click of context ID, append current ID to input
        if (message.context_id) {
          row.querySelector('[data-value="context_id"]').onclick = () => appendContextID(message.context_id);
        }

        return row;
      });

      // Add rows to page
      document.getElementById('log-data').replaceChildren(...rows);

      // Update pagination
      updatePagination({
        paginationElementId: 'pagination',
        navigateFunction: queryForLogs,
        page: messages.page,
        pages: messages.pages,
        amountVisible: isSmallScreen() ? 5 : 15,
      });

      $('.ui.dropdown').dropdown();
    },
    error: response => showErrorToast({type: 'Error Querying Logs', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * Query a list of all internal server errors listed in the log files.
 */
function queryLogErrors() {
  /**
   * Get a string which details how long ago the given date occured.
   * @param {Date} date - Reference date to format between.
   * @returns String between `date` and now.
   */
  function timeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    const units = [
      { name: 'year',   seconds: 31536000 },
      { name: 'month',  seconds: 2592000  },
      { name: 'week',   seconds: 604800   },
      { name: 'day',    seconds: 86400    },
      { name: 'hour',   seconds: 3600     },
      { name: 'minute', seconds: 60       },
      { name: 'second', seconds: 1        }
    ];

    for (const unit of units) {
      const interval = Math.floor(diffInSeconds / unit.seconds);
      if (interval > 0) {
        return `${interval} ${unit.name}${interval !== 1 ? 's' : ''} ago`;
      }
    }
    return 'Just Now';
  }

  $.ajax({
    type: 'GET',
    url: '/api/v2/logs/errors',
    /**
     * List of errors returned. Populate page.
     * @param {LogInternalServerError[]} logErrors 
     */
    success: logErrors => {
      // If there are no errors, exit
      if (logErrors.length === 0) { return; }

      // There are some errors, remove the "no errors" info message
      document.getElementById('no-internal-errors').remove();

      const errorList = document.getElementById('error-list');
      const template = document.getElementById('internal-error-template');
      logErrors.forEach(error => {
        const item = template.content.cloneNode(true);
        // Populate the item
        item.querySelector('[data-value="timestamp"]').innerText = timeAgo(new Date(error.timestamp));
        item.querySelector('[data-value="context_id"]').innerText = error.context_id;
        // When the context ID is clicked, add-to and scroll-to input
        item.querySelector('[data-value="context_id"]').onclick = () => {
          document.querySelector('input[name="context_id"]').scrollIntoView({behavior: 'smooth', block: 'start'});
          setTimeout(() => appendContextID(error.context_id), 250);
        }
        // When timestamp is clicked, update inputs
        item.querySelector('[data-value="timestamp"]').onclick = () => {
          document.querySelector('input[name="context_id"]').scrollIntoView({behavior: 'smooth', block: 'start'});
          updateTimestamp(error.timestamp);
        };
        // When the GitHub icon is clicked, query the log zip and open a new tab
        item.querySelector('.icon').onclick = () => $.ajax({
          type: 'GET',
          url: `/api/v2/logs/database-zip`,
          xhrFields: {responseType: 'blob'},
          success: logBlob => {
            downloadFileBlob('log_db.zip', logBlob);

            window.open(
              'https://github.com/TitleCardMaker/TitleCardMaker-WebUI/issues/new?'
              + 'assignees=CollinHeist&labels=bug&projects=&template=bug_report_log.yml'
              + '&title=BUG+-+&version={{ preferences.config.CURRENT_VERSION }}',
              '_blank'
            );
          },
        });

        errorList.appendChild(item);
      });
    },
  })
}

/**
 * Run the "Clean Database" scheduler task to prune old logs.
 */
function runCleanDatabaseTask() {
  const $button = $('button[onclick="runCleanDatabaseTask();"]');
  const $icon = setLoadingIcon($button.find('.icon'));
  
  $.ajax({
    type: 'PUT',
    url: '/api/v2/scheduler/task/ClearOldLogs',
    success: () => {
      showInfoToast('Clean Database task completed');
      // Refresh logs after pruning
      setTimeout(() => queryForLogs(), 1000);
    },
    error: response => showErrorToast({title: 'Error running Clean Database task', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * Download the log database as a zip file.
 */
function downloadLogDatabase() {
  const $label = $('.label[onclick="downloadLogDatabase();"]');
  const $icon = setLoadingIcon($label.find('.icon'));
  
  $.ajax({
    type: 'GET',
    url: '/api/v2/logs/database-zip',
    xhrFields: {responseType: 'blob'},
    success: logBlob => {
      downloadFileBlob('log_db.zip', logBlob);
      showInfoToast('Log database downloaded');
    },
    error: response => showErrorToast({title: 'Error downloading log database', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * Prune logs before the selected date.
 */
function pruneLogsByDate() {
  const dateInput = document.getElementById('prune-date-input');
  const selectedDate = dateInput.value;
  
  if (!selectedDate) {
    showErrorToast({title: 'No date selected', message: 'Please select a date before pruning logs.'});
    return;
  }
  
  // The Semantic UI calendar outputs in 'YYYY-MM-DDTHH:mm:ss' format (ISO 8601 without timezone)
  // FastAPI can parse this format directly, but we'll ensure it's valid
  let dateToPrune;
  try {
    // Try parsing the date to validate it
    const date = new Date(selectedDate);
    if (isNaN(date.getTime())) {
      throw new Error('Invalid date');
    }
    // Use the date string directly if it's already in ISO format, otherwise convert
    // The calendar formatter outputs 'YYYY-MM-DDTHH:mm:ss' which is valid ISO 8601
    if (selectedDate.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)) {
      dateToPrune = selectedDate;
    } else {
      // Fallback: convert to ISO 8601
      dateToPrune = date.toISOString();
    }
  } catch (error) {
    showErrorToast({title: 'Invalid date', message: 'Please select a valid date.'});
    return;
  }
  
  const $button = $('button[onclick="pruneLogsByDate();"]');
  const $icon = setLoadingIcon($button.find('.icon'));
  
  $.ajax({
    type: 'DELETE',
    url: `/api/v2/logs/prune?delete_before=${encodeURIComponent(dateToPrune)}`,
    success: () => {
      showInfoToast('Logs pruned successfully');
      // Refresh logs after pruning
      setTimeout(() => queryForLogs(), 1000);
    },
    error: response => showErrorToast({title: 'Error pruning logs', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * Initialize the page. This queries for logs, initializes dropdowns, and
 * initializes the after/before calendar inputs.
 */
function initAll() {
  $('.ui.dropdown').dropdown();
  queryForLogs();
  queryLogErrors();

  // Initialize date range calendars
  $('#date-after').calendar({
    type: 'datetime',
    endCalendar: $('#date-before'),
    maxDate: new Date(), // Cannot select dates after today
    formatter: {
      datetime: 'YYYY-MM-DDTHH:mm:ss', // ISO 8601
    }
  });
  $('#date-before').calendar({
    type: 'datetime',
    startCalendar: $('#date-after'),
    maxDate: new Date(), // Cannot select dates after today
    formatter: {
      datetime: 'YYYY-MM-DDTHH:mm:ss', // ISO 8601
    }
  });
  
  // Initialize prune date calendar
  $('#prune-date').calendar({
    type: 'datetime',
    maxDate: new Date(), // Cannot select dates after today
    formatter: {
      datetime: 'YYYY-MM-DDTHH:mm:ss', // ISO 8601
    }
  });
}
