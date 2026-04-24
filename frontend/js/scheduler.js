/**
 * Get a string of the difference between the given datetime string and
 * the current time. Only up to the two highest intervals are returned.
 * @param {string} next_run - String representation of when the next run will
 * occur.
 * @returns {string} String representation of the difference between now and
 * the next run.
 */
function timeDiffString(next_run) {
  const nextRun = new Date(next_run);

  // Get current time, 
  const now = new Date();
  const diffSeconds = Math.floor((nextRun - now) / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  // Create string for next run time, only show up to two time units
  const timeUnits = [];
  if (diffDays > 1) { timeUnits.push(`<span class="ui red text">${diffDays}</span> days`); }
  else if (diffDays > 0) { timeUnits.push(`<span class="ui red text">${diffDays}</span> day`); }
  if (diffHours % 24 > 1) { timeUnits.push(`<span class="ui green text">${diffHours%24}</span> hours`); }
  else if (diffHours % 24 > 0) { timeUnits.push(`<span class="ui green text">${diffHours%24}</span> hour`); }
  if (diffMinutes % 60 > 1) { timeUnits.push(`<span class="ui blue text">${diffMinutes%60}</span> minutes`); }
  else if (diffMinutes % 60 > 0) { timeUnits.push(`<span class="ui blue text">${diffMinutes%60}</span> minute`); }
  if (diffSeconds % 60 > 1) { timeUnits.push(`<span class="ui teal text">${diffSeconds%60}</span> seconds`); }
  else if (diffSeconds % 60 > 0) { timeUnits.push(`<span class="ui teal text">${diffSeconds%60}</span> second`); }

  return timeUnits.slice(0, 2).join(', ');
}

/**
 * Get a string representation of the given frequency.
 * @param {int} freq - Frequency (in seconds).
 * @param {int} top - Maximum number of units to include in the output. Highest
 * order units are shown first.
 * @returns {string} String representation of the frequency.
 */
function timeFreqString(freq, top=-1) {
  const seconds = Math.floor(freq);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const timeUnits = [];
  if (days > 0) { timeUnits.push(`${days} days`); }
  if (hours % 24 > 0) { timeUnits.push(`${hours%24} hours`); }
  if (minutes % 60 > 0) { timeUnits.push(`${minutes%60} minutes`); }
  if (seconds % 60 > 0 || timeUnits.length === 0) { timeUnits.push(`${seconds%60} seconds`); }
  
  if (top > 0) { return timeUnits.slice(0, top).join(', '); }
  else { return timeUnits.join(', '); }
}

/**
 * Reschedule all tasks on this page. This reads the text contents of
 * each row of the table for the API request. A separate request is
 * submitted for each row.
 */
function updateScheduledTasks() {
  $('#task-table tr').each((index, row) => {
    const taskId = row.dataset.id;
    const update_crontab = document.querySelector(`tr[data-id="${taskId}"] > td[data-column="schedule"]`).innerText;

    // Submit API request to reschedule this task
    $.ajax({
      type: 'PATCH',
      url: `/api/v2/scheduler/task/${taskId}?update_crontab=${update_crontab}`,
      contentType: 'application/json',
      error: response => showErrorToast({title: 'Error Recheduling Task', response}),
    });
  });
  setTimeout(() => {
    showInfoToast('Saved Schedules');
    const url = new URL(window.location.href);
    url.searchParams.set('restart_required', 'true');
    window.location.href = url.toString();
  }, 1500);
}

/**
 * Submit the API request to toggle the Scheduler type. If successful, this
 * reloads the page.
 */
function toggleScheduleType() {
  document.getElementById('toggle-button').classList.add('loading');
  $.ajax({
    type: 'POST',
    url: '/api/v2/scheduler/type/toggle',
    success: () => {
      showInfoToast({title: 'Updated Scheduler', message: 'Reloading page..'});
      setTimeout(() => location.reload(), 2000);
    },
    error: response => {
      document.getElementById('toggle-button').classList.remove('loading');
      showErrorToast({title: 'Error Changing Scheduler', response});
    },
  });
}

/**
 * Set the visual state of a run button.
 * @param {HTMLButtonElement} btn - The .sched-run-btn element.
 * @param {boolean} running - Whether the task is currently running.
 */
function setRunBtnState(btn, running) {
  if (running) {
    btn.classList.add('running');
    btn.querySelector('i').className = 'sync loading icon';
    btn.querySelector('.sched-run-label').textContent = 'Running\u2026';
  } else {
    btn.classList.remove('running');
    btn.querySelector('i').className = 'play icon';
    btn.querySelector('.sched-run-label').textContent = 'Run';
  }
}

/**
 * Submit the API request to run the Task with the given ID.
 * @param {string} taskId - ID of the Task which is being run.
 */
function runTask(taskId) {
  const btn = document.querySelector(`tr[data-id="${taskId}"] .sched-run-btn`);
  if (!btn || btn.classList.contains('running')) {
    showInfoToast(`Task ${taskId} is already running`);
    return;
  }
  setRunBtnState(btn, true);
  showInfoToast(`Running Task ${taskId}`);
  $.ajax({
    type: 'PUT',
    url: `/api/v2/scheduler/task/${taskId}`,
    success: task => {
      showInfoToast(`Task ${taskId} Completed`);
      document.querySelector(`tr[data-id="${taskId}"] td[data-column="previous_duration"]`).innerHTML
        = timeFreqString(task.previous_duration, 2);
    },
    error: response => showErrorToast({title: 'Error Running Task', response}),
    complete: () => setRunBtnState(btn, false),
  });
}

/**
 * Decode the given crontab expression into a human-readable string.
 * @param {string} crontab - Crontab to decode
 * @returns {string} Decoded cron expression HTML.
 */
function decodeCrontab(crontab) {
  try {
    return `<span class="ui text">${cronstrue.toString(crontab)}</span>`;
  } catch (error) {
    return '<span class="ui red text">Invalid Expression</span>';
  }
}

/**
 * Initialize all elements on the page. This creates the Scheduled Task
 * table.
 */
async function initAll() {
  const url = new URL(window.location.href);
  if (url.searchParams.has('restart_required')) {
    const restartBanner = document.getElementById('restart-required-banner');
    if (restartBanner !== null) {
      restartBanner.style.display = '';
    }
    url.searchParams.delete('restart_required');
    window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
  }

  const taskTable = document.getElementById('task-table');
  const rowTemplate = document.getElementById('task-template');
  if (taskTable === null || rowTemplate === null) { return; }

  const allTasks = await fetch('/api/v2/scheduler/scheduled').then(resp => resp.json());
  const rows = allTasks.map(task => {
    const row = rowTemplate.content.cloneNode(true);
    row.querySelector('tr').dataset.id = task.id;
    const runBtn = row.querySelector('.sched-run-btn');
    if (task.running) {
      setRunBtnState(runBtn, true);
    } else {
      runBtn.onclick = () => runTask(task.id);
    }
    row.querySelector('td[data-column="description"]').innerHTML = task.description;
    // Fill out schedule row
    if (row.querySelector('td[data-column="schedule"]')) {
      // Add human-readable time
      const span = row.querySelector('td[data-column="schedule"] span');
      const scheduleStringRow = row.querySelector('td[data-column="schedule-string"]');
      scheduleStringRow.innerHTML = decodeCrontab(task.crontab);
      span.innerText = task.crontab;

      // Update tooltip on edit
      span.addEventListener('keyup', function() {
        scheduleStringRow.innerHTML = decodeCrontab(span.innerText);
      });
    // Fill out frequency row
    } else {
      row.querySelector('td[data-column="frequency"]').innerHTML = `<span contenteditable="true">${timeFreqString(task.frequency)}</span>`;
    }
    if (task.previous_duration === null || task.previous_duration < 0) {
      row.querySelector('td[data-column="previous_duration"]').innerHTML = '-';
    } else {
      row.querySelector('td[data-column="previous_duration"]').innerHTML = timeFreqString(task.previous_duration, 2);
    }
    row.querySelector('td[data-column="next_run"]').innerHTML = `in ${timeDiffString(task.next_run)}`;

    return row;
  });
  taskTable.replaceChildren(...rows);
}
